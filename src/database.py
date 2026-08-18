from pymongo import MongoClient

from src.config import (
    BATCH_RUNS_COLLECTION,
    DAILY_SUMMARY_COLLECTION,
    MEASUREMENTS_COLLECTION,
    MONGO_DATABASE,
    MONGO_URI,
)


# Create one MongoDB client when the application starts.
# PyMongo will reuse its internal connection pool for all database operations.
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=3000,
)

# Select the database configured for the application.
db = client[MONGO_DATABASE]


def get_database():
    """
    Return the MongoDB database used by the application.
    """

    return db


def get_batch_runs_collection():
    """
    Return the collection used to track daily batch execution.
    """

    # Select the batch status collection.
    collection = db[BATCH_RUNS_COLLECTION]

    # Each calendar-day batch should have only one tracking document.
    collection.create_index(
        "batch_id",
        unique=True,
    )

    return collection


def get_measurements_collection():
    """
    Return the collection containing cleaned hourly measurements.
    """

    # Select the hourly air-quality measurements collection.
    collection = db[MEASUREMENTS_COLLECTION]

    # A city can have only one measurement for a specific timestamp.
    # This also prevents duplicates when a failed batch is retried.
    collection.create_index(
        [
            ("City", 1),
            ("Datetime", 1),
        ],
        unique=True,
    )

    return collection


def get_daily_summary_collection():
    """
    Return the collection containing daily city summaries.
    """

    # Select the daily aggregated summary collection.
    collection = db[DAILY_SUMMARY_COLLECTION]

    # Each city should have only one summary for each calendar day.
    collection.create_index(
        [
            ("City", 1),
            ("Date", 1),
        ],
        unique=True,
    )

    return collection


def save_batch_run(metadata: dict):
    """
    Save or update the status of one batch.
    """

    collection = get_batch_runs_collection()

    collection.update_one(
        {"batch_id": metadata["batch_id"]},
        {"$set": metadata},
        upsert=True,
    )

def should_process_batch(batch_id: str) -> bool:
    """
    Return True if a batch should be processed.

    New or failed batches should run.
    Successful batches should be skipped.
    """

    collection = get_batch_runs_collection()

    batch_run = collection.find_one(
        {"batch_id": batch_id}
    )

    # The batch has never been processed.
    if batch_run is None:
        return True

    # Only completed batches should be skipped.
    return batch_run["status"] != "success"





