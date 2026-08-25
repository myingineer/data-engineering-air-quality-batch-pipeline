# Air Quality Batch Processing Pipeline
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![ETL](https://img.shields.io/badge/ETL-555555?style=flat-square)
![Batch Processing](https://img.shields.io/badge/Batch_Processing-005571?style=flat-square)

A data-engineering batch pipeline for processing hourly air-quality measurements from cities across India.

The system processes source data in **daily batches**, validates and cleans records, stores hourly measurements in MongoDB, creates daily city-level summaries, tracks batch execution status, supports safe recovery after failures, and provides system-health reporting and city AQI comparisons.

## Project Purpose

The pipeline supports environmental monitoring and public-health analysis across multiple cities.

It separates two different concepts:

* **Air-quality health** — represented by AQI and pollutant measurements.
* **System health** — indicates whether the data-processing system is operating correctly and whether the latest available data was processed successfully.

Daily city summaries allow analysts or regional teams to compare cities using consistent metrics without repeatedly aggregating the complete hourly dataset.

## Dataset

The project uses the **Air Quality Data in India** dataset from Kaggle:

[Air Quality Data in India — Kaggle](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india/data?select=city_hour.csv)

The repository includes:

```text
data/sample_city_hour.csv
```

The sample contains:

* 1,300 records
* 26 cities
* 50 reproducibly sampled records per city

The Dockerized pipeline uses this sample dataset by default. Therefore, the repository can be cloned and executed without downloading the complete dataset.

The full `city_hour.csv` file is not committed to the repository because of its size.

### Using the Full Dataset

To process the complete dataset:

1. Download `city_hour.csv` from the Kaggle source above.
2. Place it in:

```text
data/city_hour.csv
```

3. Change the pipeline input from:

```text
DATA_FILE=data/sample_city_hour.csv
```

to:

```text
DATA_FILE=data/city_hour.csv
```

The complete dataset used during development contains:

* 707,875 hourly records
* 26 cities
* 16 columns
* 2,009 calendar days
* Date range: January 2015 to July 2020

## Batch Design

One batch represents **one calendar day** containing all available hourly measurements for that date.

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

The number of cities and records varies between days depending on the available source data.

A complete day with all 26 cities can contain up to:

```text
26 cities × 24 hourly records = 624 records
```

## Architecture

```text
Docker Compose
│
├── MongoDB Container
│   │
│   └── init_mongo.js
│       ├── initializes collections
│       └── creates required indexes
│
└── Python Pipeline Container
    │
    └── source dataset
         │
         v
    Daily Batch Creation
         │
         v
    Schema Validation & Cleaning
         │
         ├───────────────> Rejected Records
         │
         v
    Cleaned Hourly Measurements
         │
         v
    MongoDB hourly_measurements
         │
         v
    Daily City Aggregation
         │
         v
    MongoDB daily_city_summary

Batch processing metadata
         │
         v
    MongoDB batch_runs
```

## Main Features

* Daily batch processing
* MongoDB database initialization through Docker
* Schema validation
* Datetime and numeric validation
* Invalid-record rejection
* MongoDB persistence
* Idempotent loading using upserts
* Retry of failed batches on subsequent pipeline runs
* Automatic skipping of successful batches
* Persistent batch-status tracking
* Processing start and finish timestamps
* Daily city-level aggregation
* Intermediate representation for analytical queries
* Data-completeness indicators
* User-visible system-health reporting
* City AQI comparison
* AQI visualization
* Persistent application logging
* Docker and Docker Compose support
* Automated tests

## MongoDB Collections

The system uses three MongoDB collections with separate responsibilities.

### `hourly_measurements`

Stores the cleaned hourly air-quality data.

Each document represents:

> one city at one specific timestamp

The collection contains fields such as:

```text
City
Datetime
PM2.5
PM10
NO
NO2
NOx
NH3
CO
SO2
O3
Benzene
Toluene
Xylene
AQI
AQI_Bucket
```

The unique key is:

```text
City + Datetime
```

This prevents duplicate hourly measurements when a batch is retried.

### `daily_city_summary`

Stores one aggregated document per city per calendar day.

Each document represents:

> one city for one day

The unique key is:

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

`measurement_count` and `aqi_reading_count` also provide information about data completeness.

For example:

```text
measurement_count = 24
aqi_reading_count = 23
```

means 24 hourly records were available for the city, but only 23 contained an AQI value.

This collection acts as an **intermediate representation**. City comparisons and visualizations can query the daily summaries instead of repeatedly aggregating the complete hourly dataset.

### `batch_runs`

Stores processing metadata for each daily batch.

Each document represents:

> the processing state of one calendar-day batch

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

The three collections therefore have different purposes:

```text
hourly_measurements
→ detailed cleaned air-quality data

daily_city_summary
→ aggregated analytical data

batch_runs
→ processing state and system-health metadata
```

## Database Initialization

MongoDB runs inside an official Docker container.

The database setup script is:

```text
scripts/init_mongo.js
```

Docker Compose mounts this script into:

```text
/docker-entrypoint-initdb.d/
```

When MongoDB initializes a new database volume, the script creates the collections and required unique indexes.

The Python database layer also ensures that the required indexes exist before data is loaded.

MongoDB initialization scripts run automatically when the database starts with a new, empty data volume.

## Failure Recovery

Before processing a daily batch, the pipeline checks its existing state in `batch_runs`.

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

This makes processing idempotent: rerunning a failed or partially processed batch does not create duplicate measurements or summaries.

Example recovery flow:

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

Pipeline health is made user-visible through:

```text
scripts/verify_data.py
```

Run:

```bash
python3 -m scripts.verify_data
```

The system reports one of three states.

### HEALTHY

```text
MongoDB is reachable
Latest processed batch succeeded
```

### DEGRADED

```text
MongoDB is reachable
Latest batch failed or no completed data is available
```

Previously successful data remains available.

### FAILED

```text
MongoDB is unreachable
```

The health report also displays:

* successful batch count
* failed batch count
* stored measurement count
* latest processed batch
* processing timestamps
* latest successful data batch
* batch error information

A full-dataset development run produced:

```text
System status: HEALTHY
Successful batches: 2009
Failed batches: 0
Stored measurements: 707875
Latest successful batch: 2020-07-01
```

## City Comparison

Daily summaries support comparisons between cities without scanning and aggregating the entire hourly collection for every query.

Run:

```bash
python3 -m scripts.compare_cities
```

The script:

* queries `daily_city_summary`
* orders cities by average AQI
* displays AQI-reading coverage
* generates a horizontal bar chart

Using the complete dataset, `2020-05-10` contains AQI data for all 26 cities and provides a useful multi-city comparison.

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
→ structured batch state stored in MongoDB

pipeline.log
→ chronological execution history
```

Generated `.log` files are excluded from Git.

## Project Structure

```text
data-engineering-air-quality-batch-pipeline/
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
│   ├── init_mongo.js
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

The application supports the following environment variables:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=air_quality_db
DATA_FILE=data/sample_city_hour.csv
```

`DATA_FILE` determines which dataset the pipeline processes.

By default:

```text
DATA_FILE=data/sample_city_hour.csv
```

When the Python application runs inside Docker Compose, MongoDB is reached using the Compose service name:

```text
mongodb://mongodb:27017
```

instead of:

```text
mongodb://localhost:27017
```

because the Python application and MongoDB run in separate containers.

## Run with Docker

Docker is the recommended way to run the project.

Clone the repository:

```bash
git clone https://github.com/myingineer/data-engineering-air-quality-batch-pipeline.git
cd data-engineering-air-quality-batch-pipeline
```

Build and start the complete system:

```bash
docker compose up --build
```

Docker Compose automatically:

1. Starts the MongoDB container.
2. Runs `scripts/init_mongo.js` when a new MongoDB data volume is initialized.
3. Creates the required collections and indexes.
4. Waits until MongoDB is healthy.
5. Starts the Python pipeline container.
6. Loads `data/sample_city_hour.csv`.
7. Processes the sample data in daily batches.
8. Stores hourly measurements in `hourly_measurements`.
9. Creates daily city summaries in `daily_city_summary`.
10. Stores batch execution metadata in `batch_runs`.

No download of the complete dataset is required to run the sample system.

### Run with the Full Dataset

Download `city_hour.csv` from:

[Air Quality Data in India — Kaggle](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india/data?select=city_hour.csv)

Place the file in:

```text
data/city_hour.csv
```

Then change the pipeline environment setting in `docker-compose.yml` from:

```yaml
DATA_FILE: data/sample_city_hour.csv
```

to:

```yaml
DATA_FILE: data/city_hour.csv
```

Rebuild and start the system:

```bash
docker compose up --build
```

The pipeline will then process the complete dataset.

## Local Setup

Docker is still required for MongoDB, but the Python pipeline can also be executed directly on the host machine.

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

Create a local `.env` file:

```bash
cp .env.example .env
```

Start MongoDB:

```bash
docker compose up -d mongodb
```

Run the pipeline:

```bash
python3 -m src.main
```

With the default configuration, the pipeline processes:

```text
data/sample_city_hour.csv
```

To run the complete dataset locally, download `city_hour.csv`, place it in `data/`, and set:

```env
DATA_FILE=data/city_hour.csv
```

## Tests

The automated tests require MongoDB to be running because the loader tests interact with the database.

Start MongoDB if necessary:

```bash
docker compose up -d mongodb
```

Run all tests:

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

* the repository can be cloned and the sample system started using Docker;
* MongoDB is initialized automatically inside its container;
* the included sample data can be loaded automatically by the Python pipeline;
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
* AQI-reading coverage is visible alongside city summaries;
* city comparisons can be visualized;
* the pipeline can resume after interruption;
* the complete source dataset can be processed without record loss.

The complete development run confirmed:

```text
Source records:        707875
Stored measurements:   707875

Calendar-day batches:  2009
Successful batches:    2009
Failed batches:        0
```

## Author

**Alexander Soromtochukwu Emeka-Akam**  
B.Sc. Applied Artificial Intelligence  
IU International University of Applied Sciences  
Berlin, Germany

GitHub: [myingineer](https://github.com/myingineer)
