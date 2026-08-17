import os

from dotenv import load_dotenv

# Define the expected schema for the air quality data.
EXPECTED_SCHEMA = {
    "City": "string",
    "Datetime": "datetime",
    "PM2.5": "numeric",
    "PM10": "numeric",
    "NO": "numeric",
    "NO2": "numeric",
    "NOx": "numeric",
    "NH3": "numeric",
    "CO": "numeric",
    "SO2": "numeric",
    "O3": "numeric",
    "Benzene": "numeric",
    "Toluene": "numeric",
    "Xylene": "numeric",
    "AQI": "numeric",
    "AQI_Bucket": "string",
}

BATCH_STATUS_RUNNING = "running"
BATCH_STATUS_SUCCESS = "success"
BATCH_STATUS_FAILED = "failed"

BATCH_RUNS_COLLECTION = "batch_runs"

MEASUREMENTS_COLLECTION = "hourly_measurements"

DAILY_SUMMARY_COLLECTION = "daily_city_summary"

# Load environment variables from the local .env file.
load_dotenv()

# Load the MongoDB connection URI from the environment variable, with a default value.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017",
)

# Load the database name from the environment variable, with a default value.
MONGO_DATABASE = os.getenv(
    "MONGO_DATABASE",
    "air_quality_db",
)