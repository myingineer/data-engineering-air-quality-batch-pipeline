import pandas as pd

from src.aggregator import create_daily_city_summary


def test_daily_city_summary():
    """
    Hourly records from the same city and day
    should become one daily summary.
    """

    df = pd.DataFrame(
        [
            {
                "City": "Delhi",
                "Datetime": pd.Timestamp("2020-01-01 10:00:00"),
                "PM2.5": 40.0,
                "AQI": 100.0,
            },
            {
                "City": "Delhi",
                "Datetime": pd.Timestamp("2020-01-01 11:00:00"),
                "PM2.5": 60.0,
                "AQI": 140.0,
            },
        ]
    )

    summary = create_daily_city_summary(df)

    assert len(summary) == 1

    row = summary.iloc[0]

    assert row["City"] == "Delhi"
    assert row["measurement_count"] == 2
    assert row["aqi_reading_count"] == 2
    assert row["average_aqi"] == 120.0
    assert row["minimum_aqi"] == 100.0
    assert row["maximum_aqi"] == 140.0
    assert row["average_pm25"] == 50.0