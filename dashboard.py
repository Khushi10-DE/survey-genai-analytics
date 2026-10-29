import os
import requests
import streamlit as st

st.set_page_config(page_title="Survey Insights", layout="wide")
st.title("Survey Insights Dashboard")
st.caption("Demonstration dataset. Sentiment is based on numerical ratings, not AI classification.")
api = os.getenv("SURVEY_API_URL", "http://127.0.0.1:8000")
try:
    response = requests.get(f"{api}/insights", timeout=5)
    response.raise_for_status()
    data = response.json()
    c1, c2 = st.columns(2)
    c1.metric("Responses", data["total_responses"])
    c2.metric("Average rating", data["average_rating"] or "N/A")
    st.subheader("Sentiment from ratings")
    st.bar_chart(data["sentiment"])
    st.subheader("Response categories")
    st.bar_chart(data["by_category"])
    st.subheader("Summary")
    st.write(data["summary"])
except requests.RequestException as exc:
    st.error(f"Could not reach API at {api}. Start uvicorn first. ({exc})")
