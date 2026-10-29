from fastapi.testclient import TestClient
from app.main import app, analyze, load_responses

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_insights():
    r = client.get("/insights")
    assert r.status_code == 200
    assert r.json()["total_responses"] == 8
    assert r.json()["sentiment"]["positive"] == 5

def test_analysis():
    result = analyze(load_responses())
    assert result["average_rating"] == 3.62
