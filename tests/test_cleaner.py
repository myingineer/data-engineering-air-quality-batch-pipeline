import pandas as pd
import pytest

from src.cleaner import clean_batch, validate_schema


def create_test_record():
    """
    Create one valid air-quality record for cleaner tests.
    """

    return {
        "City": "Delhi",
        "Datetime": "2020-01-01 10:00:00",
        "PM2.5": 50.0,
        "PM10": 80.0,
        "NO": 10.0,
        "NO2": 20.0,
        "NOx": 30.0,
        "NH3": 5.0,
        "CO": 1.0,
        "SO2": 8.0,
        "O3": 25.0,
        "Benzene": 2.0,
        "Toluene": 3.0,
        "Xylene": 1.0,
        "AQI": 120.0,
        "AQI_Bucket": "Moderate",
    }


def test_valid_record_is_cleaned():
    """A valid record should pass through the cleaner."""

    df = pd.DataFrame([create_test_record()])

    cleaned, rejected = clean_batch(df)

    assert len(cleaned) == 1
    assert len(rejected) == 0
    assert pd.api.types.is_datetime64_any_dtype(
        cleaned["Datetime"]
    )


def test_invalid_datetime_is_rejected():
    """A record with an invalid datetime should be rejected."""

    record = create_test_record()
    record["Datetime"] = "not-a-date"

    df = pd.DataFrame([record])

    cleaned, rejected = clean_batch(df)

    assert len(cleaned) == 0
    assert len(rejected) == 1
    assert (
        rejected.iloc[0]["rejection_reason"]
        == "missing_or_invalid_identity"
    )


def test_negative_measurement_is_rejected():
    """A negative environmental measurement should be rejected."""

    record = create_test_record()
    record["PM2.5"] = -25

    df = pd.DataFrame([record])

    cleaned, rejected = clean_batch(df)

    assert len(cleaned) == 0
    assert len(rejected) == 1
    assert (
        rejected.iloc[0]["rejection_reason"]
        == "negative_measurement"
    )


def test_missing_schema_column_raises_error():
    """A batch missing an expected column should fail validation."""

    record = create_test_record()

    df = pd.DataFrame([record]).drop(
        columns=["AQI"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        validate_schema(df)