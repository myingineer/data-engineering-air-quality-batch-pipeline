from pymongo.errors import PyMongoError
import pandas as pd

from src.config import DATA_FILE
from src.database import (
    get_batch_runs_collection,
    get_database,
    get_measurements_collection,
)


def show_system_health():
    """
    Display the current health and processing coverage of the pipeline.
    """

    try:
        # Connect to MongoDB and verify that it is reachable.
        db = get_database()
        db.client.admin.command("ping")

        batch_runs = get_batch_runs_collection()
        measurements = get_measurements_collection()

        # Read only Datetime from the configured source file.
        source_data = pd.read_csv(
            DATA_FILE,
            usecols=["Datetime"],
        )

        source_data["Datetime"] = pd.to_datetime(
            source_data["Datetime"],
            errors="coerce",
        )

        # Determine which daily batches are expected from the source file.
        expected_batch_ids = (
            source_data["Datetime"]
            .dropna()
            .dt.date
            .astype(str)
            .unique()
            .tolist()
        )

        expected_batches = len(expected_batch_ids)
        latest_source_batch = max(expected_batch_ids)

        # Find the most recently processed batch.
        latest_batch = batch_runs.find_one(
            {"batch_id": {"$in": expected_batch_ids}},
            sort=[("started_at", -1)],
        )

        # Find the latest successfully processed source batch.
        latest_success = batch_runs.find_one(
            {
                "batch_id": {"$in": expected_batch_ids},
                "status": "success",
            },
            sort=[("batch_id", -1)],
        )

        # Count batch states for the currently configured source file.
        successful_batches = batch_runs.count_documents(
            {
                "batch_id": {"$in": expected_batch_ids},
                "status": "success",
            }
        )

        failed_batches = batch_runs.count_documents(
            {
                "batch_id": {"$in": expected_batch_ids},
                "status": "failed",
            }
        )

        outstanding_batches = (
            expected_batches - successful_batches
        )

        measurement_count = measurements.count_documents({})

        # Determine the overall system health.
        if latest_batch is None:
            system_status = "DEGRADED"

        elif latest_batch["status"] == "failed":
            system_status = "DEGRADED"

        elif outstanding_batches > 0:
            system_status = "DEGRADED"

        else:
            system_status = "HEALTHY"

        print(
            f"""
                === Air Quality Pipeline Health ===

                System status: {system_status}

                Database:
                MongoDB: reachable

                Batch coverage:
                Expected batches: {expected_batches}
                Successful batches: {successful_batches}
                Failed batches: {failed_batches}
                Outstanding batches: {outstanding_batches}
                Latest source batch: {latest_source_batch}

                Stored measurements:
                {measurement_count}
            """
        )

        if latest_batch:
            print(
                f"""Latest processed batch:
                    Batch ID: {latest_batch['batch_id']}
                    Status: {latest_batch['status']}
                    Started: {latest_batch.get('started_at')}
                    Finished: {latest_batch.get('finished_at')}
                """
            )

            if latest_batch.get("error_message"):
                print(
                    f"Error: {latest_batch['error_message']}"
                )

        if latest_success:
            print(
                f"""
                Latest successful data batch:
                {latest_success['batch_id']}
                """
            )

    except PyMongoError as error:
        print(
            f"""
                === Air Quality Pipeline Health ===

                System status: FAILED

                Database:
                MongoDB: unreachable

                Error:
                {error}
            """
        )


if __name__ == "__main__":
    show_system_health()