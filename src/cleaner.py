import pandas as pd

from src.config import EXPECTED_SCHEMA


def get_numeric_columns() -> list[str]:
    """Return all columns defined as numeric in the expected schema."""

    return [
        column
        for column, data_type in EXPECTED_SCHEMA.items()
        if data_type == "numeric"
    ]


def validate_schema(batch: pd.DataFrame) -> None:
    """
    Check that all columns defined in the expected schema are present.

    Raises a ValueError if required columns are missing.
    """

    expected_columns = set(EXPECTED_SCHEMA.keys())
    actual_columns = set(batch.columns)

    missing_columns = expected_columns - actual_columns

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )


def clean_batch(
    batch: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean one daily batch of air-quality records.

    Returns:
        cleaned_records:
            Records that passed validation.

        rejected_records:
            Records that failed validation.
    """

    # Work on a copy so the original DataFrame is unchanged.
    validate_schema(batch)

    cleaned = batch.copy()

    # Convert Datetime into a real datetime type.
    cleaned["Datetime"] = pd.to_datetime(
        cleaned["Datetime"],
        errors="coerce",
    )

    # Get numeric columns from the central schema.
    numeric_columns = get_numeric_columns()

    # Ensure measurement columns contain numeric values.
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce",
        )

    # Start each record without a rejection reason.
    cleaned["rejection_reason"] = None

    # City and Datetime are required.
    invalid_identity = (
        cleaned["City"].isna()
        | cleaned["City"].astype(str).str.strip().eq("")
        | cleaned["Datetime"].isna()
    )

    cleaned.loc[
        invalid_identity,
        "rejection_reason",
    ] = "missing_or_invalid_identity"

    # Missing numeric measurements are allowed,
    # but negative measurements are considered invalid.
    negative_measurement = (
        cleaned[numeric_columns]
        .lt(0)
        .any(axis=1)
    )

    cleaned.loc[
        negative_measurement
        & cleaned["rejection_reason"].isna(),
        "rejection_reason",
    ] = "negative_measurement"

    # Separate valid and rejected records.
    rejected_records = cleaned[
        cleaned["rejection_reason"].notna()
    ].copy()

    cleaned_records = cleaned[
        cleaned["rejection_reason"].isna()
    ].copy()

    # Valid records do not need rejection metadata.
    cleaned_records = cleaned_records.drop(
        columns=["rejection_reason"]
    )

    return cleaned_records, rejected_records