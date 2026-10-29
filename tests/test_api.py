
import pandas as pd
import app.main as main
from fastapi.testclient import TestClient

client = TestClient(main.app)


def sample_responses():
    """Fixed survey data for automated tests."""
    return pd.DataFrame({
        "rating": [5, 4, 3, 2, 5, 4, 3, 3],
        "category": [
            "Engineering", "HR", "Engineering", "Sales",
            "HR", "Engineering", "Sales", "HR"
        ],
        "feedback": [
            "Great workplace",
            "Supportive team",
            "Good experience",
            "Needs improvement",
            "Excellent culture",
            "Happy with my team",
            "More training needed",
            "Good communication"
        ]
    })


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_insights(monkeypatch):
    # Prevent this test from reading Google Sheets.
    monkeypatch.setattr(main, "load_responses", sample_responses)

    response = client.get("/insights")

    assert response.status_code == 200

    result = response.json()

    assert result["total_responses"] == 8
    assert result["average_rating"] == 3.62
    assert result["sentiment"]["positive"] == 4
    assert result["sentiment"]["neutral"] == 3
    assert result["sentiment"]["negative"] == 1


def test_analysis():
    result = main.analyze(sample_responses())

    assert result["total_responses"] == 8
    assert result["average_rating"] == 3.62
    assert result["sentiment"]["positive"] == 4
    assert result["sentiment"]["neutral"] == 3
    assert result["sentiment"]["negative"] == 1