db = db.getSiblingDB("air_quality_db");

db.createCollection("hourly_measurements");
db.createCollection("daily_city_summary");
db.createCollection("batch_runs");

db.hourly_measurements.createIndex(
    {
        City: 1,
        Datetime: 1
    },
    {
        unique: true
    }
);

db.daily_city_summary.createIndex(
    {
        City: 1,
        Date: 1
    },
    {
        unique: true
    }
);

db.batch_runs.createIndex(
    {
        batch_id: 1
    },
    {
        unique: true
    }
);