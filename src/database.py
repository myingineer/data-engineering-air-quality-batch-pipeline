from pymongo import MongoClient

from src.config import (
    BATCH_RUNS_COLLECTION,
    DAILY_SUMMARY_COLLECTION,
    MEASUREMENTS_COLLECTION,
    MONGO_DATABASE,
    MONGO_URI,
)

def get_database():
    """
    Connect to MongoDB and return the project database.
    """

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=3000
    )

    return client[MONGO_DATABASE]


def get_batch_runs_collection():
    """
    Return the MongoDB collection used to track batch executions.
    """

    db = get_database()

    collection = db[BATCH_RUNS_COLLECTION]

    # Each calendar day should have only one batch-tracking document.
    collection.create_index(
        "batch_id",
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


def get_measurements_collection():
    """
    Return the MongoDB collection containing hourly air-quality measurements.
    """

    db = get_database()

    collection = db[MEASUREMENTS_COLLECTION]

    # A city should have only one measurement for a specific timestamp.
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
    Return the MongoDB collection containing daily city summaries.
    """

    db = get_database()

    collection = db[DAILY_SUMMARY_COLLECTION]

    # Each city should have only one summary for each calendar date.
    collection.create_index(
        [
            ("City", 1),
            ("Date", 1),
        ],
        unique=True,
    )

    return collection

