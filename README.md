# Survey GenAI Analytics — portfolio MVP

A reproducible survey analytics starter project using **FastAPI, Pandas, Streamlit and GitHub Actions**.

> **Current implementation:** CSV-based survey ingestion, cleaning, rating-based sentiment, category counts, API and dashboard. live Google Sheets integration, Azure Functions deployment, and LLM/GenAI summaries.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. In a second terminal, activate the same environment and run:

```bash
streamlit run dashboard.py
```

## Using your own Google Forms export

Export responses as CSV from the linked Google Sheet. Rename columns to `rating`, `category`, `feedback` and save outside your public repository. Set `SURVEY_CSV` to the absolute path of your CSV, then restart the API. Never commit respondent names, email addresses or confidential feedback.

## Endpoints

- `GET /health` — service health
- `GET /responses` — cleaned responses
- `GET /insights` — rating statistics and a deterministic summary

## Architecture

Google Forms → Google Sheets → exported CSV → FastAPI/Pandas → Streamlit dashboard

## Next milestones

1. Add authenticated Google Sheets API ingestion with service-account credentials stored in environment variables, not Git.
2. Add a clearly labelled opt-in LLM summary feature; remove personal information before sending responses to any model.
3. Deploy a lightweight API endpoint to Azure Functions if you have an Azure subscription.
4. Add screenshots and a 60–90 second demo video.

## CV-ready description (after verifying the features)

Developed a FastAPI and Pandas survey analytics API with data validation, rating-based insights, Streamlit dashboard and automated tests in GitHub Actions.
