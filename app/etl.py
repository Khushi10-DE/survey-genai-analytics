from pathlib import Path
import re
import pandas as pd


DEPARTMENT_NAMES = {
    "hr": "HR",
    "human resources": "HR",
    "it": "IT",
    "information technology": "IT",
    "sales": "Sales",
    "finance": "Finance",
    "operations": "Operations",
}

MISSING_FEEDBACK = {"", "na", "n/a", "none", "null", "nan"}


def clean_text(value):
    """Remove unnecessary whitespace from text."""
    if pd.isna(value):
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def clean_department(value):
    """Standardize department names."""
    department = clean_text(value)

    return DEPARTMENT_NAMES.get(
        department.lower(),
        department or "Unknown"
    )


def clean_feedback(value):
    """Normalize empty or placeholder feedback."""
    feedback = clean_text(value)

    if feedback.lower() in MISSING_FEEDBACK:
        return ""

    return feedback


def transform_survey_data(raw_df):
    """
    Clean survey records and return:
    1. Valid cleaned responses
    2. Invalid responses
    3. Data quality report

    Expected columns: rating, category, feedback
    """

    required_columns = {"rating", "category", "feedback"}

    missing = required_columns - set(raw_df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df = raw_df.copy()

    extracted_rows = len(df)

    df["category"] = df["category"].apply(clean_department)
    df["feedback"] = df["feedback"].apply(clean_feedback)

    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )

    valid_rating = (
        df["rating"].notna()
        & df["rating"].between(1, 5)
        & df["rating"].mod(1).eq(0)
    )

    invalid_df = df.loc[~valid_rating].copy()
    cleaned_df = df.loc[valid_rating].copy()

    cleaned_df["rating"] = cleaned_df["rating"].astype(int)

    quality_report = {
        "extracted_rows": extracted_rows,
        "valid_rows": len(cleaned_df),
        "invalid_rows": len(invalid_df),
        "empty_feedback_rows": int(
            cleaned_df["feedback"].eq("").sum()
        ),
        "duplicate_candidates": int(
            cleaned_df.duplicated(
                subset=["rating", "category", "feedback"],
                keep=False
            ).sum()
        ),
    }

    return cleaned_df, invalid_df, quality_report


def save_etl_outputs(cleaned_df, invalid_df, quality_report):
    """Save ETL results to separate local files."""

    output_dir = Path(__file__).resolve().parents[1] / "data" / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / "cleaned_responses.csv"
    invalid_path = output_dir / "invalid_responses.csv"
    report_path = output_dir / "quality_report.json"

    cleaned_df.to_csv(cleaned_path, index=False)
    invalid_df.to_csv(invalid_path, index=False)

    import json

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(quality_report, file, indent=4)

    return {
        "cleaned_file": str(cleaned_path),
        "invalid_file": str(invalid_path),
        "report_file": str(report_path)
    }
    

def save_etl_outputs(cleaned_df, invalid_df, quality_report):
    """Save cleaned data, invalid data, and the quality report."""

    import json

    output_dir = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / "cleaned_responses.csv"
    invalid_path = output_dir / "invalid_responses.csv"
    report_path = output_dir / "quality_report.json"

    cleaned_df.to_csv(cleaned_path, index=False)
    invalid_df.to_csv(invalid_path, index=False)

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(quality_report, file, indent=4)

    return {
        "cleaned_file": str(cleaned_path),
        "invalid_file": str(invalid_path),
        "report_file": str(report_path)
    }