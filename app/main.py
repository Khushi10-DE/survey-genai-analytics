from app.gemini_analysis import analyze_feedback_with_gemini
from app.etl import transform_survey_data, save_etl_outputs
from app.azure_storage import upload_etl_files
from pathlib import Path
import os
import pandas as pd

from fastapi import FastAPI, HTTPException
from google.auth import default
from googleapiclient.discovery import build
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    PROJECT_ROOT / ".env",
    override=False
)

app = FastAPI(title="Survey GenAI Analytics", version="0.2.0")

BASE = Path(__file__).resolve().parents[1]


def load_google_sheets():
    """Read private Google Forms responses through Google Sheets API."""

    spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not spreadsheet_id:
        raise ValueError("GOOGLE_SHEET_ID environment variable is missing.")

    credentials, _ = default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    service = build("sheets", "v4", credentials=credentials)

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="A1:Z1000"
    ).execute()

    rows = result.get("values", [])

    if not rows:
        return pd.DataFrame()

    headers = rows[0]

    # Google Sheets API can omit trailing empty cells.
    records = [
        (row + [""] * len(headers))[:len(headers)]
        for row in rows[1:]
    ]

    return pd.DataFrame(records, columns=headers)


def load_responses():
    """Convert Google Form responses into the analytics data model."""
    source = os.environ.get("SURVEY_SOURCE", "csv").lower()

    if source == "google":
        raw = load_google_sheets()

        if raw.empty:
            return pd.DataFrame(
                columns=["rating", "feedback", "category"]
            )

        # Match the actual Google Form question headers.
        def find_column(phrase):
            matches = [
                col for col in raw.columns
                if phrase.lower() in col.lower()
            ]
            if not matches:
                raise ValueError(
                    f"Could not find a Google Sheets column containing "
                    f"'{phrase}'. Available columns: {list(raw.columns)}"
                )
            return matches[0]

        rating_col = find_column("overall work experience")
        category_col = find_column("department")
        feedback_col = find_column("improvements would you suggest")

        df = pd.DataFrame({
            "rating": raw[rating_col],
            "category": raw[category_col],
            "feedback": raw[feedback_col],
        })

    else:
        path = Path(
            os.environ.get(
                "SURVEY_CSV",
                str(BASE / "data" / "sample_responses.csv")
            )
        )

        if not path.is_file():
            raise FileNotFoundError(f"Survey CSV not found: {path}")

        df = pd.read_csv(path)

    # ETL: Transform and validate the extracted survey data
    cleaned_df, invalid_df, quality_report = transform_survey_data(df)

    return cleaned_df


def analyze(df):
    """Deterministic baseline analysis; Gemini integration comes next."""

    total = len(df)

    if total == 0:
        return {
            "total_responses": 0,
            "average_rating": None,
            "sentiment": {},
            "by_category": {},
            "summary": "No valid responses."
        }

    labels = df["rating"].apply(
        lambda n: (
            "positive" if n >= 4
            else "negative" if n <= 2
            else "neutral"
        )
    )

    sentiment = {
        k: int((labels == k).sum())
        for k in ("positive", "neutral", "negative")
    }

    by_category = {
        str(k): int(v)
        for k, v in df["category"].value_counts().items()
    }

    most_common = max(by_category, key=by_category.get)

    summary = (
        f"Analyzed {total} survey responses. "
        f"Average rating: {df['rating'].mean():.1f}/5. "
        f"Positive: {sentiment['positive']}; "
        f"neutral: {sentiment['neutral']}; "
        f"negative: {sentiment['negative']}. "
        f"Most common category: {most_common}."
    )

    return {
        "total_responses": total,
        "average_rating": round(float(df["rating"].mean()), 2),
        "sentiment": sentiment,
        "by_category": by_category,
        "summary": summary
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/responses")
def responses():
    try:
        return load_responses().to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


@app.get("/insights")
def insights():
    try:
        return analyze(load_responses())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc
        
@app.get("/debug/source")
def debug_source():
    return {
        "source": os.environ.get("SURVEY_SOURCE", "csv"),
        "sheet_id_configured": bool(os.environ.get("GOOGLE_SHEET_ID")),
        "credentials_configured": bool(
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        ),
        "app_version": app.version
    }
    
@app.get("/ai-insights")
def ai_insights():
    try:
        df = load_responses()
        return analyze_feedback_with_gemini(
            df.to_dict(orient="records")
        )
    except Exception as e:
        print(f"GEMINI ERROR: {type(e).__name__}: {e}", flush=True)

    raise HTTPException(
        status_code=500,
        detail="AI analysis failed. Check the VS Code terminal."
    )
        

@app.get("/etl-report")
def etl_report():
    try:
        source = os.environ.get("SURVEY_SOURCE", "csv").lower()

        if source == "google":
            raw = load_google_sheets()

            if raw.empty:
                return {
                    "extracted_rows": 0,
                    "valid_rows": 0,
                    "invalid_rows": 0,
                    "empty_feedback_rows": 0,
                    "duplicate_candidates": 0
                }

            def find_column(phrase):
                matches = [
                    col for col in raw.columns
                    if phrase.lower() in col.lower()
                ]

                if not matches:
                    raise ValueError(
                        f"Missing Google Sheets column: {phrase}"
                    )

                return matches[0]

            df = pd.DataFrame({
                "rating": raw[
                    find_column("overall work experience")
                ],
                "category": raw[
                    find_column("department")
                ],
                "feedback": raw[
                    find_column("improvements would you suggest")
                ]
            })

        else:
            path = Path(
                os.environ.get(
                    "SURVEY_CSV",
                    str(BASE / "data" / "sample_responses.csv")
                )
            )

            df = pd.read_csv(path)

        cleaned_df, invalid_df, report = transform_survey_data(df)

        return report

    except Exception:
        import logging
        logging.exception("ETL report failed")

        raise HTTPException(
            status_code=500,
            detail="ETL report failed. Check the terminal."
        )


@app.post("/run-etl")
def run_etl():
    try:
        source = os.environ.get("SURVEY_SOURCE", "csv").lower()

        if source == "google":
            raw = load_google_sheets()

            if raw.empty:
                df = pd.DataFrame(
                    columns=["rating", "category", "feedback"]
                )
            else:
                def find_column(phrase):
                    matches = [
                        col for col in raw.columns
                        if phrase.lower() in col.lower()
                    ]

                    if not matches:
                        raise ValueError(
                            f"Missing survey column: {phrase}"
                        )

                    return matches[0]

                df = pd.DataFrame({
                    "rating": raw[
                        find_column("overall work experience")
                    ],
                    "category": raw[
                        find_column("department")
                    ],
                    "feedback": raw[
                        find_column("improvements would you suggest")
                    ]
                })

        else:
            path = Path(
                os.environ.get(
                    "SURVEY_CSV",
                    str(BASE / "data" / "sample_responses.csv")
                )
            )

            df = pd.read_csv(path)

        # One transformation produces all three ETL outputs.
        cleaned_df, invalid_df, report = transform_survey_data(df)

        paths = save_etl_outputs(
            cleaned_df,
            invalid_df,
            report
        )

        return {
            "status": "success",
            "quality_report": report,
            "files": paths
        }

    except Exception:
        import logging
        logging.exception("ETL execution failed")

        raise HTTPException(
            status_code=500,
            detail="ETL execution failed. Check the terminal."
        )

@app.post("/run-pipeline")
def run_pipeline():
    """
    Run the ETL process, then upload its outputs to Azure.
    """

    #reuse existing ETL endpoint function
    etl_result = run_etl()

    # Upload the newly generated files
    azure_result = upload_etl_files()

    return {
        "status": "success",
        "etl": etl_result,
        "azure": azure_result,
    }
