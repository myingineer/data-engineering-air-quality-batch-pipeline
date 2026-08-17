# Air Quality Batch Processing Pipeline

A data-engineering batch pipeline for processing hourly air-quality measurements from cities across India.

The system processes the source dataset in **daily batches**, validates and cleans records, stores hourly measurements in MongoDB, creates daily city-level summaries, tracks batch execution status, supports safe recovery after failures, and provides system-health reporting and city AQI comparisons.

## Project Purpose

The pipeline supports environmental monitoring and public-health analysis across multiple cities.

It separates two different concepts:

* **Air-quality health** — represented by AQI and pollutant measurements.
* **System health** — indicates whether the data-processing system is operating correctly and whether the latest available data was processed successfully.

Daily city summaries allow analysts or regional teams to compare cities using a consistent set of metrics without repeatedly querying the complete hourly dataset.

## Dataset

The project uses the **Air Quality Data in India** dataset from Kaggle.

Source:

[Air Quality Data in India — Kaggle](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india/data?select=city_hour.csv)

The full `city_hour.csv` file is **not included in this repository**.

A representative development sample is included:

```text
data/sample_city_hour.csv
```

The sample contains:

* 1,300 records
* 26 cities
* 50 reproducibly sampled records per city

To run the complete pipeline:

1. Download `city_hour.csv` from the Kaggle dataset.
2. Place it in:

```text
data/city_hour.csv
```

The full dataset used during development contains:

* 707,875 hourly records
* 26 cities
* 16 columns
* 2,009 calendar days
* Date range: January 2015 to July 2020

## Batch Design

One batch represents **one calendar day** of all available hourly measurements.

Example:

```text
Batch ID: 2020-05-10

Start: 2020-05-10 00:00:00
End:   2020-05-11 00:00:00
```

The batch boundary is:

```text
Datetime >= batch start
Datetime < next calendar day
```

The number of cities and records varies between days depending on available source data.

A complete day with all 26 cities can contain up to:

```text
26 cities × 24 hourly records = 624 records
```

## Architecture

```text
city_hour.csv
      |
      v
Daily Batch Creation
      |
      v
Schema Validation & Cleaning
      |
      +---------------------+
      |                     |
      v                     v
Valid Records          Rejected Records
      |
      v
Hourly Measurement Loading
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

## Main Features

* Daily batch processing
* Schema validation
* Datetime and numeric validation
* Invalid-record rejection
* MongoDB persistence
* Idempotent loading using upserts
* Automatic retry of failed batches
* Automatic skipping of successful batches
* Persistent batch-status tracking
* Processing start and finish timestamps
* Daily city-level aggregation
* Data-completeness indicators
* User-visible system-health reporting
* City AQI comparison
* AQI visualization
* Persistent application logging
* Docker and Docker Compose support
* Automated tests

## MongoDB Collections

### `hourly_measurements`

Stores cleaned hourly air-quality measurements.

Each document represents one city at one specific timestamp.

Unique key:

```text
City + Datetime
```

This prevents duplicate measurements when batches are retried.

### `daily_city_summary`

Stores one aggregated document per city per calendar day.

Unique key:

```text
City + Date
```

Summary fields include:

```text
measurement_count
aqi_reading_count
average_aqi
minimum_aqi
maximum_aqi
average_pm25
```

`measurement_count` and `aqi_reading_count` also provide data-quality information.

For example:

```text
measurement_count = 24
aqi_reading_count = 23
```

means 24 hourly records were available, but only 23 contained an AQI value.

This collection acts as an **intermediate representation**, allowing city comparisons and visualizations without repeatedly aggregating the full hourly dataset.

### `batch_runs`

Stores operational information about each daily batch.

Fields include:

```text
batch_id
start_datetime
end_datetime
record_count
city_count
cleaned_count
rejected_count
inserted_count
modified_count
matched_count
summary_count
summary_inserted_count
summary_modified_count
summary_matched_count
status
started_at
finished_at
error_message
```

Possible batch states are:

```text
running
success
failed
```

## Failure Recovery

Before processing a batch, the pipeline checks its existing state in `batch_runs`.

```text
Batch not found  → process
Batch failed     → retry
Batch successful → skip
```

Hourly measurements use:

```text
City + Datetime
```

as a unique key.

Daily summaries use:

```text
City + Date
```

as a unique key.

Both are loaded using MongoDB upserts.

This means a failed or partially completed batch can be rerun without creating duplicate records.

For example:

```text
Batch starts
    ↓
status = running
    ↓
processing fails
    ↓
status = failed
    ↓
problem is corrected
    ↓
pipeline restarted
    ↓
failed batch detected
    ↓
batch retried
    ↓
status = success
```

Previously successful batches are skipped.

## System Health

Pipeline health is made visible through:

```text
scripts/verify_data.py
```

Run:

```bash
python3 -m scripts.verify_data
```

Possible system states are:

### HEALTHY

```text
MongoDB is reachable
Latest processed batch succeeded
```

### DEGRADED

```text
MongoDB is reachable
Latest batch failed or current data processing is incomplete
```

Previously successful data remains available.

### FAILED

```text
MongoDB is unreachable
```

The health report also shows:

* successful batch count
* failed batch count
* stored measurement count
* latest processed batch
* processing timestamps
* latest successful data batch
* batch error information

After processing the complete dataset during development:

```text
System status: HEALTHY
Successful batches: 2009
Failed batches: 0
Stored measurements: 707875
Latest successful batch: 2020-07-01
```

## City Comparison

Daily summaries support comparisons between cities without scanning the entire hourly collection.

Run:

```bash
python3 -m scripts.compare_cities
```

The script:

* queries `daily_city_summary`
* orders cities by average AQI
* displays AQI-reading coverage
* generates a horizontal bar chart

For example, `2020-05-10` contains AQI data for all 26 cities and provides a useful multi-city comparison.

This supports collaborative analysis between environmental or public-health teams working across different cities or regions.

## Logging

Pipeline execution is logged to:

```text
logs/pipeline.log
```

Example:

```text
INFO | pipeline | Batch 2015-01-08 started with 168 records
INFO | pipeline | Batch 2015-01-08 succeeded: 168 cleaned, 0 rejected, 168 inserted, 7 summaries
```

The two monitoring mechanisms have different purposes:

```text
batch_runs
→ structured current batch state in MongoDB

pipeline.log
→ chronological execution history
```

Generated `.log` files are excluded from Git.

## Project Structure

```text
air_quality_batch_pipeline/
│
├── data/
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

Create a local `.env` file:

```bash
cp .env.example .env
```

Example:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=air_quality_db
```

When the Python application runs inside Docker Compose, it connects to MongoDB through the Compose service name:

```text
mongodb://mongodb:27017
```

## Local Setup

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download `city_hour.csv` from Kaggle and place it in:

```text
data/city_hour.csv
```

Start MongoDB:

```bash
docker compose up -d mongodb
```

Run the pipeline:

```bash
python3 -m src.main
```

## Docker Setup

Build the pipeline image:

```bash
docker compose build pipeline
```

Run the pipeline:

```bash
docker compose run --rm pipeline
```

Docker Compose runs:

```text
pipeline container
      ↓
mongodb:27017
      ↓
MongoDB container
```

MongoDB data is stored in a persistent Docker volume.

Application logs are mounted to:

```text
logs/
```

on the host system.

## Tests

Run all automated tests:

```bash
pytest -v
```

The test suite covers:

* valid record cleaning
* invalid datetime rejection
* negative measurement rejection
* missing-schema detection
* MongoDB measurement insertion
* duplicate-safe measurement loading
* daily city aggregation

Current test result:

```text
7 passed
```

## Success Criteria

The project is considered successful when:

* source data is divided into clearly bounded daily batches;
* each batch knows its start and end boundaries;
* valid hourly measurements are stored without duplication;
* invalid records can be identified and separated;
* failed batches can be retried safely;
* successful batches are not unnecessarily reprocessed;
* batch status and failures are visible to the user;
* system availability can be reported as HEALTHY, DEGRADED, or FAILED;
* daily city summaries provide an intermediate representation for analysis;
* different cities can be compared using consistent daily metrics;
* AQI coverage is visible alongside city summaries;
* city comparisons can be visualized;
* the pipeline can resume after interruption;
* the complete source dataset can be processed without record loss.

The complete development run confirmed:

```text
Source records:       707875
Stored measurements:  707875

Calendar-day batches: 2009
Successful batches:   2009
Failed batches:       0
```

## Author

**Alexander Soromtochukwu Emeka-Akam**  
B.Sc. Applied Artificial Intelligence  
IU International University of Applied Sciences  
Berlin, Germany  

GitHub: [GitHub Profile](YOUR_GITHUB_URL)  
LinkedIn: [LinkedIn Profile](YOUR_LINKEDIN_URL)
