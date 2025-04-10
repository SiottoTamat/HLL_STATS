import pandas as pd
import matplotlib.pyplot as plt
from datetime import date


def plot_player_data(
    df: pd.DataFrame,
    timeframe_group_by: str,
    lim_start: date | None = None,
    lim_end: date | None = None,
    metrics: str | list | None = None,
    drop_zeroes=True,
    player_names: dict | None = None,
    constant_multiplier=int | None,
) -> None:
    assert timeframe_group_by in [
        "week",
        "month",
    ], "timeframe_group_by must be 'week' or 'month'"

    player_id = df["player_id"].unique()[0]
    player_name = player_id
    if player_names:
        player_name = player_names[player_id]

    if drop_zeroes:
        df = df[df.value != 0]

    if constant_multiplier:
        # df["value"] = df["value"] * constant_multiplier
        df.loc[df["metric"] == "list Apolo kpm", "value"] *= constant_multiplier

    # Apply date range filtering
    if lim_start is not None:
        df = df[df["date"] >= pd.to_datetime(lim_start)]
    if lim_end is not None:
        df = df[df["date"] <= pd.to_datetime(lim_end)]
    print(df["date"].head())
    print(df["date"].dtype)
    print(df["date"].isna().sum())

    df["date"] = pd.to_datetime(
        df["date"], format="%Y-%m-%dT%H-%M-%S", errors="coerce"
    ).dt.tz_localize(None)
    df = df.dropna(subset=["date"])
    print(df["date"].dtype)
    if timeframe_group_by == "week":
        df["group"] = df["date"].dt.to_period("W").dt.start_time

    elif timeframe_group_by == "month":
        df["group"] = df["date"].dt.to_period("M").dt.start_time

    grouped = df.groupby(["group", "metric"])["value"].mean().reset_index()
    pivot_df = grouped.pivot(index="group", columns="metric", values="value")

    # Plot
    plt.style.use("seaborn-darkgrid")
    pivot_df.plot(figsize=(12, 6), marker="o")
    plt.title(f"Player: {player_name} - {timeframe_group_by.capitalize()}ly Metrics")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.grid(True)
    plt.legend(title="Metric")
    # Modify the legend labels by removing 'list ' from the metric names
    handles, labels = plt.gca().get_legend_handles_labels()
    labels = [label.replace("list ", "") for label in labels]

    # Set the modified labels in the legend
    plt.legend(handles, labels)
    plt.tight_layout()
    plt.show()


def main():
    pass


if __name__ == "__main__":
    main()
