import pandas as pd
from datetime import datetime, timezone
from src.cleaner import clean_batch
from src.aggregator import create_daily_city_summary
import logging
from src.logging_config import setup_logging

from src.database import (
    should_process_batch,
    save_batch_run
)

from src.config import (
    BATCH_STATUS_RUNNING,
    BATCH_STATUS_SUCCESS,
    BATCH_STATUS_FAILED,
)

from src.loader import (
    load_daily_summaries,
    load_measurements,
)

setup_logging()

logger = logging.getLogger("pipeline")

def create_daily_batches(
    df: pd.DataFrame,
):
    """
    Split air-quality records into calendar-day batches.

    Each batch contains all available city measurements
    for one date.
    """

    df = df.copy()

    df["Datetime"] = pd.to_datetime(
        df["Datetime"],
        errors="coerce",
    )

    # Group by the calendar date without adding batch_date
    # to the measurement records themselves.
    for batch_date, batch in df.groupby(
        df["Datetime"].dt.date
    ):
        yield batch_date, batch



def get_batch_metadata(
    batch_date,
    batch: pd.DataFrame,
) -> dict:
    """
    Create metadata describing one daily batch.
    """

    start_datetime = pd.Timestamp(batch_date)
    end_datetime = start_datetime + pd.Timedelta(days=1)

    return {
        "batch_id": str(batch_date),
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "record_count": len(batch),
        "city_count": batch["City"].nunique(),
        "status": BATCH_STATUS_RUNNING,
        "started_at": datetime.now(timezone.utc),
        "finished_at": None,
    }


def process_batch(
    batch_date,
    batch: pd.DataFrame,
):
    """
    Clean, load, and aggregate one daily batch
    while tracking its processing status.
    """

    metadata = get_batch_metadata(
        batch_date,
        batch,
    )

    logger.info(
        "Batch %s started with %s records",
        metadata["batch_id"],
        metadata["record_count"],
    )

    # Record that processing has started.
    save_batch_run(metadata)

    try:
        # Step 1: Clean and validate the batch.
        cleaned_records, rejected_records = clean_batch(batch)

        # Step 2: Store cleaned hourly measurements.
        measurement_result = load_measurements(
            cleaned_records
        )

        # Step 3: Create the daily city summaries.
        daily_summary = create_daily_city_summary(
            cleaned_records
        )

        # Step 4: Store the daily city summaries.
        summary_result = load_daily_summaries(
            daily_summary
        )

        # Record cleaning results.
        metadata["cleaned_count"] = len(cleaned_records)
        metadata["rejected_count"] = len(rejected_records)

        # Record hourly measurement loading results.
        metadata["inserted_count"] = (
            measurement_result["inserted_count"]
        )
        metadata["modified_count"] = (
            measurement_result["modified_count"]
        )
        metadata["matched_count"] = (
            measurement_result["matched_count"]
        )

        # Record summary results separately.
        metadata["summary_count"] = len(daily_summary)
        metadata["summary_inserted_count"] = (
            summary_result["inserted_count"]
        )
        metadata["summary_modified_count"] = (
            summary_result["modified_count"]
        )
        metadata["summary_matched_count"] = (
            summary_result["matched_count"]
        )

        metadata["status"] = BATCH_STATUS_SUCCESS
        metadata["error_message"] = None
        metadata["finished_at"] = datetime.now(timezone.utc)

        save_batch_run(metadata)

        logger.info(
            "Batch %s succeeded: %s cleaned, %s rejected, %s inserted, %s summaries",
            metadata["batch_id"],
            metadata["cleaned_count"],
            metadata["rejected_count"],
            metadata["inserted_count"],
            metadata["summary_count"],
        )

        return cleaned_records, rejected_records, metadata

    except Exception as error:
        metadata["status"] = BATCH_STATUS_FAILED
        metadata["error_message"] = str(error)
        metadata["finished_at"] = datetime.now(timezone.utc)

        save_batch_run(metadata)

        logger.error(
            "Batch %s failed: %s",
            metadata["batch_id"],
            metadata["error_message"],
        )

        return None, None, metadata


def run_pipeline(
    df: pd.DataFrame,
    max_batches: int | None = None,
):
    """
    Process daily batches, skipping batches that already succeeded.
    """

    processed_count = 0

    for batch_date, batch in create_daily_batches(df):
        batch_id = str(batch_date)

        if not should_process_batch(batch_id):
            logger.info(
                "Skipping batch %s - already successful",
                batch_id,
            )
            continue

        _, _, metadata = process_batch(
            batch_date,
            batch,
        )

        print(
            f"Batch {batch_id} - "
            f"status: {metadata['status']}"
        )

        processed_count += 1

        if (
            max_batches is not None
            and processed_count >= max_batches
        ):
            break


if __name__ == "__main__":
    df = pd.read_csv("data/city_hour.csv")

    run_pipeline(df)