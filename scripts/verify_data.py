from pymongo.errors import PyMongoError

from src.database import (
    get_batch_runs_collection,
    get_database,
    get_measurements_collection,
)


def show_system_health():
    """
    Display the current health and processing state of the pipeline.
    """

    try:
        # Connect to MongoDB and verify that it is reachable.
        db = get_database()
        db.client.admin.command("ping")

        batch_runs = get_batch_runs_collection()
        measurements = get_measurements_collection()

        # Find the most recently processed batch.
        latest_batch = batch_runs.find_one(
            sort=[("started_at", -1)]
        )

        # Find the latest batch that completed successfully.
        latest_success = batch_runs.find_one(
            {"status": "success"},
            sort=[("batch_id", -1)],
        )

        # Determine the overall system health.
        if latest_batch is None:
            system_status = "DEGRADED"
        elif latest_batch["status"] == "failed":
            system_status = "DEGRADED"
        else:
            system_status = "HEALTHY"

        # Collect summary statistics.
        successful_batches = batch_runs.count_documents(
            {"status": "success"}
        )

        failed_batches = batch_runs.count_documents(
            {"status": "failed"}
        )

        measurement_count = measurements.count_documents({})

        # Display the main health report.
        print(
            f"""
                === Air Quality Pipeline Health ===

                System status: {system_status}

                Database:
                MongoDB: reachable

                Batch summary:
                Successful batches: {successful_batches}
                Failed batches: {failed_batches}

                Stored measurements:
                {measurement_count}
            """
        )

        # Display details about the most recently processed batch.
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

        # Display the latest successfully available data.
        if latest_success:
            print(
                f"""
                    Latest successful data batch:
                    {latest_success['batch_id']}
                """
            )

    except PyMongoError as error:
        # If MongoDB itself cannot be reached, the system is unavailable.
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