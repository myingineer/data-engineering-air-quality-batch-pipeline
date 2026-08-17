# Air Quality Batch Processing Pipeline

A batch data-engineering pipeline for processing hourly air-quality measurements from multiple Indian cities.

The system processes the source dataset in **daily batches**, cleans and validates the records, stores hourly measurements in MongoDB, creates daily city-level summaries, tracks batch execution status, supports safe retries, and provides system-health and city-comparison outputs.

## Architecture

```text
city_hour.csv
      |
      v
Daily Batch Creation
      |
      v
Cleaning & Validation
      |
      +--------------------+
      |                    |
      v                    v
Hourly Measurements   Rejected Records
      |
      v
Daily City Aggregation
      |
      v
Daily City Summary
      |
      v
MongoDB
├── hourly_measurements
├── daily_city_summary
└── batch_runs
```

## Batch Design

One batch represents **one calendar day** of all available hourly measurements.

Example:

```text
Batch ID: 2020-05-10

Start: 2020-05-10 00:00:00
End:   2020-05-11 00:00:00
```

The number of cities and records can vary by day.

The dataset contains:

- 707,875 hourly records
- 26 cities
- 2,009 calendar-day batches
- Date range: 2015-01-01 to 2020-07-01

## Main Features

- Daily batch processing
- Schema validation
- Datetime and numeric data cleaning
- Rejection of invalid records
- MongoDB persistence
- Idempotent loading using upserts
- Automatic retry of failed batches
- Successful batches skipped on restart
- Batch execution tracking
- Daily city-level aggregation
- System-health reporting
- City AQI comparison and visualization
- Docker support
- Automated tests

## MongoDB Collections

### `hourly_measurements`

Stores cleaned hourly air-quality measurements.

Unique key:

```text
City + Datetime
```

This prevents duplicate measurements when a batch is retried.

### `daily_city_summary`

Stores one aggregated record per city per day.

Unique key:

```text
City + Date
```

Example summary fields:

```text
measurement_count
aqi_reading_count
average_aqi
minimum_aqi
maximum_aqi
average_pm25
```

This collection acts as an intermediate representation for faster city comparisons and visualizations.

### `batch_runs`

Stores operational information about each daily batch.

Example fields:

```text
batch_id
start_datetime
end_datetime
record_count
city_count
cleaned_count
rejected_count
inserted_count
matched_count
summary_count
status
started_at
finished_at
error_message
```

Batch statuses are:

```text
running
success
failed
```

## Failure Recovery

Before processing a batch, the pipeline checks `batch_runs`.

```text
Batch not found  → process
Batch failed     → retry
Batch successful → skip
```

Hourly measurements and daily summaries use MongoDB upserts, so rerunning a partially processed batch does not create duplicate records.

## Project Structure

```text
air_quality_batch_pipeline/
│
├── data/
│   ├── city_hour.csv
│   ├── sample_city_hour.csv
│   └── README.md
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── cleaner.py
│   ├── loader.py
│   ├── aggregator.py
│   └── logging_config.py
│
├── scripts/
│   ├── __init__.py
│   ├── verify_data.py
│   └── compare_cities.py
│
├── tests/
│   ├── __init__.py
│   ├── test_cleaner.py
│   ├── test_loader.py
│   └── test_aggregator.py
│
├── logs/
│   └── .gitkeep
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Environment Configuration

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Example:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=air_quality_db
```

When the pipeline runs inside Docker Compose, it connects to MongoDB using:

```text
mongodb://mongodb:27017
```

## Run Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start MongoDB:

```bash
docker compose up -d mongodb
```

Run the pipeline:

```bash
python3 -m src.main
```

## Run with Docker

Build the pipeline image:

```bash
docker compose build pipeline
```

Run the pipeline:

```bash
docker compose run --rm pipeline
```

MongoDB data is persisted using a Docker volume.

## System Health

Run:

```bash
python3 -m scripts.verify_data
```

The health report shows:

- MongoDB availability
- overall system status
- successful batches
- failed batches
- stored measurements
- latest processed batch
- latest successful batch

Possible system states:

```text
HEALTHY
MongoDB is reachable and the latest batch succeeded.

DEGRADED
MongoDB is reachable but the latest batch failed or no successful data is available.

FAILED
MongoDB is unreachable.
```

After the complete dataset was processed:

```text
Successful batches: 2009
Failed batches: 0
Stored measurements: 707875
Latest successful batch: 2020-07-01
System status: HEALTHY
```

## City Comparison

Run:

```bash
python3 -m scripts.compare_cities
```

The script queries `daily_city_summary` rather than recalculating results from all hourly records.

For example, `2020-05-10` contains AQI data for all 26 cities and can be used to compare their daily average AQI values.

The script displays the comparison in the terminal and generates a horizontal bar chart.

## Logging

Pipeline execution is written to:

```text
logs/pipeline.log
```

Example:

```text
INFO | pipeline | Batch 2015-01-08 started with 168 records
INFO | pipeline | Batch 2015-01-08 succeeded: 168 cleaned, 0 rejected, 168 inserted, 7 summaries
```

Logs provide a chronological execution history, while `batch_runs` stores structured batch state in MongoDB.

## Tests

Run all tests:

```bash
pytest -v
```

The automated tests cover:

- valid record cleaning
- invalid datetime rejection
- negative measurement rejection
- schema validation
- MongoDB measurement insertion
- duplicate-safe loading
- daily city aggregation


## Author

**Alexander Soromtochukwu Emeka-Akam**

B.Sc. Applied Artificial Intelligence  
IU International University of Applied Sciences  
Berlin, Germany

- GitHub: [GitHub Profile](https://github.com/myingineer/)
- LinkedIn: [LinkedIn Profile](https://www.linkedin.com/in/myingineer/)