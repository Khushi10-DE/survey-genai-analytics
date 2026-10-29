
import streamlit as st
import pandas as pd
import plotly.express as px
import requests

API_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Survey GenAI Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Survey GenAI Analytics Platform")
st.caption("Employee Experience & Workplace Feedback Dashboard")


@st.cache_data(ttl=60)
def fetch_responses():
    response = requests.get(f"{API_URL}/responses", timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_ai_insights():
    response = requests.get(
        f"{API_URL}/ai-insights",
        timeout=(10, 240)
    )
    response.raise_for_status()
    return response.json()


def to_dataframe(payload):
    if isinstance(payload, list):
        return pd.DataFrame(payload)

    if isinstance(payload, dict):
        for key in ("responses", "data", "items"):
            if isinstance(payload.get(key), list):
                return pd.DataFrame(payload[key])

    return pd.DataFrame()


st.sidebar.header("Dashboard Controls")

if st.sidebar.button("🔄 Refresh Survey Data"):
    st.cache_data.clear()
    st.rerun()

try:
    payload = fetch_responses()
    df = to_dataframe(payload)

except requests.exceptions.RequestException as exc:
    st.error("Cannot connect to the FastAPI backend.")
    st.info(
        "Start FastAPI on port 8001, then refresh this page."
    )
    st.code("python -m uvicorn app.main:app --reload --port 8001")
    st.stop()

if df.empty:
    st.warning("No survey responses were returned.")
    st.write("API response:", payload)
    st.stop()

st.subheader("Survey Responses")

# Show the data returned by the API.
st.dataframe(df, use_container_width=True)

# Locate expected fields without assuming exact capitalization.
column_lookup = {
    str(column).strip().lower(): column
    for column in df.columns
}

rating_col = column_lookup.get("rating")
category_col = column_lookup.get("category")
feedback_col = column_lookup.get("feedback")

if rating_col:
    df[rating_col] = pd.to_numeric(
        df[rating_col], errors="coerce"
    )

total_responses = len(df)
average_rating = (
    df[rating_col].mean()
    if rating_col and df[rating_col].notna().any()
    else None
)

col1, col2, col3 = st.columns(3)

col1.metric("Total Responses", total_responses)

col2.metric(
    "Average Rating",
    f"{average_rating:.2f} / 5"
    if average_rating is not None
    else "N/A"
)

col3.metric(
    "Departments / Categories",
    df[category_col].nunique()
    if category_col
    else "N/A"
)

st.divider()
st.subheader("📈 Survey Analytics")

if rating_col and category_col:
    chart_data = (
        df.dropna(subset=[rating_col])
        .groupby(category_col, as_index=False)[rating_col]
        .mean()
    )

    fig = px.bar(
        chart_data,
        x=category_col,
        y=rating_col,
        title="Average Rating by Department / Category",
        labels={
            category_col: "Department / Category",
            rating_col: "Average Rating"
        }
    )
    fig.update_yaxes(range=[0, 5])
    st.plotly_chart(fig, use_container_width=True)

if rating_col:
    fig = px.histogram(
        df.dropna(subset=[rating_col]),
        x=rating_col,
        title="Rating Distribution",
        nbins=5
    )
    st.plotly_chart(fig, use_container_width=True)

if feedback_col:
    st.subheader("💬 Employee Feedback")
    feedback = df[feedback_col].dropna().astype(str)
    feedback = feedback[feedback.str.strip() != ""]
    st.dataframe(
        pd.DataFrame({"Feedback": feedback}),
        use_container_width=True,
        hide_index=True
    )

st.divider()
st.subheader("🤖 Gemini AI Insights")

st.info(
    "Click the button to request AI analysis. "
    "This may take some time and uses your Gemini API quota."
)

if st.button("✨ Generate AI Insights"):
    with st.spinner("Gemini is analyzing survey feedback..."):
        try:
            insights = fetch_ai_insights()
            st.session_state["ai_insights"] = insights
        except requests.exceptions.RequestException as exc:
            st.error(f"AI analysis request failed: {exc}")

if "ai_insights" in st.session_state:
    insights = st.session_state["ai_insights"]

    if isinstance(insights, dict):
        for key, value in insights.items():
            st.markdown(f"### {key.replace('_', ' ').title()}")
            if isinstance(value, (dict, list)):
                st.json(value)
            else:
                st.write(value)
    else:
        st.write(insights)

st.caption(
    "Data source: FastAPI | AI: Google Gemini | "
    "Cloud storage: Azure Data Lake Gen2 | "
    "Orchestration: Azure Data Factory"
)
