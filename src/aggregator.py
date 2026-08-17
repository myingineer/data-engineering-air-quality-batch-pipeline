import pandas as pd


def create_daily_city_summary(
    cleaned_records: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create one daily summary per city from cleaned hourly measurements.
    """

    df = cleaned_records.copy()

    # Normalize each timestamp to the beginning of its calendar day.
    df["Date"] = df["Datetime"].dt.normalize()

    # Create one summary row for each city and date.
    summary = (
        df.groupby(["City", "Date"])
        .agg(
            measurement_count=("Datetime", "size"),
            aqi_reading_count=("AQI", "count"),
            average_aqi=("AQI", "mean"),
            minimum_aqi=("AQI", "min"),
            maximum_aqi=("AQI", "max"),
            average_pm25=("PM2.5", "mean"),
        )
        .reset_index()
    )

    return summary