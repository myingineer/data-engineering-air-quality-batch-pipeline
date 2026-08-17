from datetime import datetime

import matplotlib.pyplot as plt

from src.database import get_daily_summary_collection


def compare_cities(date: str):
    """
    Display and visualize average AQI values
    for all cities on a given date.
    """

    collection = get_daily_summary_collection()

    query_date = datetime.strptime(
        date,
        "%Y-%m-%d",
    )

    summaries = list(
        collection.find(
            {
                "Date": query_date,
                "average_aqi": {"$ne": None},
            },
            {"_id": 0},
        ).sort("average_aqi", -1)
    )

    if not summaries:
        print(f"No AQI summary data found for {date}")
        return

    # Display the comparison in the terminal.
    print(f"\n=== City AQI Comparison: {date} ===\n")

    for summary in summaries:
        print(
            f"{summary['City']:20} | "
            f"Average AQI: {summary['average_aqi']:.2f} | "
            f"Readings: {summary['aqi_reading_count']}"
        )

    # Prepare values for the visualization.
    cities = [
        summary["City"]
        for summary in summaries
    ]

    average_aqi = [
        summary["average_aqi"]
        for summary in summaries
    ]

    # Create a horizontal bar chart.
    plt.figure(figsize=(10, 9))

    plt.barh(
        cities,
        average_aqi,
    )

    plt.xlabel("Average AQI")
    plt.ylabel("City")
    plt.title(
        f"Average AQI by City — {date}"
    )

    # Highest AQI should appear at the top.
    plt.gca().invert_yaxis()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    compare_cities("2020-05-10")