import pandas as pd

from src.database import get_measurements_collection
from src.loader import load_measurements


TEST_CITY = "TestCity"
TEST_DATETIME = pd.Timestamp("2099-01-01 12:00:00")


def create_test_measurement() -> pd.DataFrame:
    """
    Create one measurement used only for loader tests.
    """

    return pd.DataFrame(
        [
            {
                "City": TEST_CITY,
                "Datetime": TEST_DATETIME,
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
        ]
    )


def remove_test_measurement():
    """
    Remove the temporary test document from MongoDB.
    """

    collection = get_measurements_collection()

    collection.delete_many(
        {"City": TEST_CITY}
    )


def test_new_measurement_is_inserted():
    """A new City + Datetime measurement should be inserted."""

    remove_test_measurement()

    df = create_test_measurement()

    result = load_measurements(df)

    assert result["inserted_count"] == 1

    remove_test_measurement()


def test_duplicate_measurement_is_not_inserted_again():
    """
    Loading the same City + Datetime twice should not create a duplicate.
    """

    remove_test_measurement()

    df = create_test_measurement()

    first_result = load_measurements(df)
    second_result = load_measurements(df)

    assert first_result["inserted_count"] == 1
    assert second_result["inserted_count"] == 0
    assert second_result["matched_count"] == 1

    remove_test_measurement()