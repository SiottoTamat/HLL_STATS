from pathlib import Path
import json
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import pandas as pd

import Utils


def _get_last_analysis_date(analysis_folder: str | Path) -> date:
    """
    Get the last analysis date from the analysis files and the plot files.

    The function reads the analysis files and the plot files and returns the
    last date that an analysis covers an entire month.

    Args:
        analysis_folder: The folder containing the analysis files.
        plots_folder: The folder containing the plot files.

    Returns:
        The last date that an analysis covers an entire month.
    """

    analysis_folder = Path(analysis_folder)

    analysis_files = list(analysis_folder.glob("*_ANALYSIS.json"))

    last_analysis_year_month = analysis_files[-1].stem[:10]
    a_year, a_month, a_day = map(int, last_analysis_year_month.split("-"))

    #  check what is the last analysis that covers an entire month
    last_analysis_date = date(a_year, a_month, a_day)
    # if the last analysis is not the last day of the month, subtract one month

    _, last_day = calendar.monthrange(a_year, a_month)
    if last_analysis_date.day < last_day:
        last_analysis_date -= relativedelta(months=1)
        last_analysis_date = last_analysis_date.replace(day=1)

    return last_analysis_date


def _get_months_to_generate(
    plots_folder: str | Path, last_analysis_date: date, overwrite: bool = False
) -> list[tuple[int, int]] | None:
    """
    Get the list of months to generate plots for.

    The function takes into account the dates of the analysis files and the
    existing plot files and returns the list of months that need to be
    generated. If overwrite is False and the plot files are already up to
    date, the function returns None.

    Args:
        plots_folder: The folder where the plot files are stored.
        last_analysis_date: The date of the last analysis file.
        overwrite: If True, the function will generate plots even if they already exist.

    Returns:
        A list of tuples with the year and month of the months to generate
        plots for. If overwrite is False and the plots are already up to date,
        the function returns None.
    """
    big_bang = date(
        2022, 3, 1
    )  # the start date for all G&W matches with MATCH START and MATCH ENDED

    plot_files = list(plots_folder.glob("*_plots.json"))
    last_plot_year_month = plot_files[-1].stem[:7]
    if last_plot_year_month == f"{last_analysis_date.year}_{last_analysis_date.month}":
        if not overwrite:
            print("Plots are already up to date. Skipping generation.")
            return None

    if overwrite:
        year_month_till_today = [
            (year, month)
            for year, month in Utils.month_year_iter(big_bang, last_analysis_date)
        ]
    else:
        year, month = map(int, last_plot_year_month.split("-"))
        start_date = date(year, month, 1) + relativedelta(months=1)
        year_month_till_today = [
            (year, month)
            for year, month in Utils.month_year_iter(start_date, last_analysis_date)
        ]

    return year_month_till_today


def _generate_monthly_plots(
    analysis_folder: str | Path,
    plots_folder: str | Path,
    year_month_till_today: list[tuple[int, int]],
    filter: dict | None = None,
    filter_name: str | None = None,
) -> None:
    for year, month in year_month_till_today:

        analysis_grouped_by_month = {}

        for file in Utils.grab_games_by_dates(analysis_folder, year, month):
            analysis_grouped_by_month = get_plot_from_analysis_list(
                Utils.openfile(file), analysis_grouped_by_month, filter
            )

        plotfile = Path(plots_folder / f"{year}_{month:02}-{filter_name}_plots.json")
        with plotfile.open("w", encoding="utf-8") as f:
            json.dump(analysis_grouped_by_month, f, indent=4)


def create_plots(
    analysis_folder: str | Path,
    plots_folder: str | Path,
    filter: dict | None = None,
    filter_name: str | None = None,
    overwrite: bool = False,
) -> None:
    """
    Creates monthly plots from a folder of analysis files.

    The code reads all the analysis files in the given folder and for each file
    it groups the data by month. It then creates a new plot file for each month
    and dumps the grouped data into it.

    Args:
        analysis_folder: The folder containing the analysis files.
        plots_folder: The folder where the plots files will be saved.
        filter: A dictionary with player ids as keys and names as values. If not
            None, the function will only use the players in the filter.
            ex: FILTER = { id: name, id2: name2, ... }
        overwrite: If True, the function will overwrite existing plot files.
    """

    plots_folder = Path(plots_folder)
    analysis_folder = Path(analysis_folder)

    last_analysis_date = _get_last_analysis_date(analysis_folder)
    year_month_till_today = _get_months_to_generate(
        plots_folder, last_analysis_date, overwrite
    )
    _generate_monthly_plots(
        analysis_folder, plots_folder, year_month_till_today, filter, filter_name
    )


def get_plot_from_analysis_list(
    list_of_game_analysis: list[dict],
    out_dict: dict,
    filters_dict: dict | None = None,
    accept_seeding=False,
    accept_incomplete=False,
    take_zeroes=False,
) -> dict:

    if not isinstance(list_of_game_analysis, list):
        list_of_game_analysis = [list_of_game_analysis]

    result = out_dict

    for analysis in list_of_game_analysis:
        if (accept_seeding or not analysis["seeding match"]) and (
            accept_incomplete or not analysis["incomplete game"]
        ):
            if filters_dict == None:
                filters_dict = analysis["players"]
            grabs = [
                x
                for x in analysis.keys()
                if x
                not in [
                    "start date",
                    "players",
                    "seeding match",
                    "incomplete game",
                    "map",
                    "date",
                    "game time",
                    "result allies",
                    "result axis",
                ]
            ]

            for grab in grabs:

                for player in analysis[grab].keys():

                    if player in filters_dict.keys():
                        # if take_zeroes or analysis[grab][player] > 0:
                        result.setdefault(player, {}).setdefault(grab, {})[
                            analysis["start date"]
                        ] = analysis[grab][player]
                    # else:

                    #     if take_zeroes or analysis[grab][player] > 0:
                    #         result[grab].setdefault("not_filter", {}).setdefault(
                    #             player, {}
                    #         )[analysis["start date"]] = analysis[grab][player]
    return result


def grab_player_plot(
    player_id: str,
    folder: Path | str,
    plots: str | list = [],
    month: str = None,
    day: str = None,
) -> dict:
    folder = Path(folder)
    files = Utils.grab_games_by_dates(folder, month, day, separator="-")
    result = {}
    for file in files:
        data = Utils.openfile(file)
        if not plots:
            plots = list(data.keys())[0]
        if player_id in data:
            for plot in plots:
                for key, value in data[player_id][plot].items():
                    result.setdefault(player_id, {}).setdefault(plot, {})[key] = value
    return result


def player_plots_from_fileplot(
    folder_plots: str | Path,
    player_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    plots: str | list = [],
) -> dict:

    if isinstance(plots, str):
        plots = [plots]
    if not start_date:
        start_date = date(2022, 3, 1)
    if not end_date:
        end_date = date.today()
    months = [
        f"{year}-{month:02}"
        for year, month in list(Utils.month_year_iter(start_date, end_date))
    ]

    file_months = [
        file
        for month in months
        for file in Path(folder_plots).glob(f"{month}*_plots.json")
    ]
    all_months_player_data = {player_id: {}}
    for plot in plots:
        all_months_player_data[player_id][plot] = {}
    for file in file_months:

        data = Utils.openfile(file)
        if player_id in data:
            for plot in plots:

                all_months_player_data[player_id][plot] = Utils.deep_merge(
                    all_months_player_data[player_id][plot], data[player_id][plot]
                )
    return all_months_player_data


def pandarize_plots(player_id: str, plots: str | list, data: dict) -> pd.DataFrame:
    if isinstance(plots, str):
        plots = [plots]
    rows = []
    for metric in plots:
        metric_data = data.get(player_id, {}).get(metric, {})
        for date, value in metric_data.items():
            rows.append(
                {"player_id": player_id, "metric": metric, "date": date, "value": value}
            )
    df = pd.DataFrame(rows)
    return df.sort_values("date").reset_index(drop=True)


def main():
    pass


if __name__ == "__main__":
    main()
