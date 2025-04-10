import talk_to_server
from pathlib import Path
from datetime import datetime, timedelta, date
import json

import Utils
import Logs_Utils
import Analysis_Utils
import Statistics
import make_plot

from All_names_ESPT_members import (
    all_ESPT_members_names as ESPT,
)  # if you have a list of people you care about


def main():
    out_folder_historical_logs = Path(r"Z:\G&W_Data\sequential_game_logs\single_days")
    out_folder_game_logs = Path(r"Z:\G&W_Data\sequential_game_logs\single_games")
    out_folder_analysis = Path(r"Z:\G&W_Data\sequential_game_logs\analysis")
    out_folder_plots = Path(r"Z:\G&W_Data\sequential_game_logs\plots")
    ESPT_filter = {x: v[0] for x, v in ESPT.items()}

    update_logs = False
    split_logs_to_games = False
    create_analysis = False
    create_monthly_plots = False
    extract_player_plot = True

    metrics = ["list Apolo kpm", "list kpm", "list dpm"]

    if update_logs:

        last_log_file = sorted(out_folder_historical_logs.glob("*.json"))[-1]
        last_log_time = Utils.openfile(last_log_file)[-1][
            "event_time"
        ]  # "2025-04-08T17:16:52"
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        talk_to_server.download_sequential_logs(
            out_folder_historical_logs, last_log_time, yesterday
        )

    if split_logs_to_games:

        Logs_Utils.merge_logs_to_games(
            out_folder_historical_logs,
            out_folder_game_logs,
            overwrite=False,
        )

    if create_analysis:
        Analysis_Utils.refill_analysis_folder(out_folder_analysis, out_folder_game_logs)

    if create_monthly_plots:
        Statistics.create_plots(
            out_folder_analysis, out_folder_plots, ESPT_filter, filter_name="ESPT"
        )
    if extract_player_plot:

        this_player = ""  # here you put the player steamid

        start_date = date(2024, 1, 1)
        end_date = date(2025, 3, 1)
        player = Statistics.player_plots_from_fileplot(
            out_folder_plots,
            this_player,
            plots=metrics,
            start_date=start_date,
            end_date=end_date,
        )
        with open(f"{this_player}_stats.json", "w", encoding="utf-8") as f:
            json.dump(player, f, indent=4)
    if extract_player_plot:

        df = Statistics.pandarize_plots(this_player, metrics, player)
        make_plot.plot_player_data(
            df,
            timeframe_group_by="week",
            player_names=ESPT_filter,
            constant_multiplier=2.5,
        )
        print("done")


if __name__ == "__main__":
    main()
