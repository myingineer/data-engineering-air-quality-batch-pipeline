import pandas as pd
from pymongo import UpdateOne

from src.database import (
    get_daily_summary_collection,
    get_measurements_collection,
)



def load_measurements(cleaned_records: pd.DataFrame) -> dict:
    """
    Load cleaned air-quality records into MongoDB.

    Existing City + Datetime records are updated.
    New records are inserted.
    """

    collection = get_measurements_collection()

    if cleaned_records.empty:
        return {
            "inserted_count": 0,
            "modified_count": 0,
            "matched_count": 0,
        }

    # Convert missing Pandas values to None for MongoDB.
    records = (
        cleaned_records
        .astype(object)
        .where(pd.notna(cleaned_records), None)
        .to_dict("records")
    )

    operations = []

    for record in records:
        # Convert Pandas Timestamp to Python datetime.
        if isinstance(record["Datetime"], pd.Timestamp):
            record["Datetime"] = record["Datetime"].to_pydatetime()

        operations.append(
            UpdateOne(
                {
                    "City": record["City"],
                    "Datetime": record["Datetime"],
                },
                {
                    "$set": record,
                },
                upsert=True,
            )
        )

    result = collection.bulk_write(
        operations,
        ordered=False,
    )

    return {
        "inserted_count": result.upserted_count,
        "modified_count": result.modified_count,
        "matched_count": result.matched_count,
    }


def load_daily_summaries(summary: pd.DataFrame) -> dict:
    """
    Load daily city summaries into MongoDB.

    Existing City + Date summaries are updated.
    New summaries are inserted.
    """

    collection = get_daily_summary_collection()

    if summary.empty:
        return {
            "inserted_count": 0,
            "modified_count": 0,
            "matched_count": 0,
        }

    # Convert Pandas missing values to None for MongoDB.
    records = (
        summary
        .astype(object)
        .where(pd.notna(summary), None)
        .to_dict("records")
    )

    operations = []

    for record in records:

        # Convert Pandas Timestamp to Python datetime.
        if isinstance(record["Date"], pd.Timestamp):
            record["Date"] = record["Date"].to_pydatetime()

        operations.append(
            UpdateOne(
                {
                    "City": record["City"],
                    "Date": record["Date"],
                },
                {
                    "$set": record,
                },
                upsert=True,
            )
        )

    result = collection.bulk_write(
        operations,
        ordered=False,
    )

    return {
        "inserted_count": result.upserted_count,
        "modified_count": result.modified_count,
        "matched_count": result.matched_count,
    }