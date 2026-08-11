import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="AI PR Review Bot — Analytics", layout="wide")


def sqlalchemy_url():
    database_url = os.environ["DATABASE_URL"]
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@st.cache_data(ttl=60)
def load_runs():
    engine = create_engine(sqlalchemy_url())
    with engine.connect() as conn:
        return pd.read_sql(
            "select * from review_runs order by created_at desc limit 500", conn
        )


st.title("AI PR Review Bot — Analytics")

df = load_runs()

if df.empty:
    st.info("No review runs logged yet. Open or update a PR to generate data.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total runs", len(df))
col2.metric("Completed", int((df["status"] == "completed").sum()))
col3.metric("Failed", int((df["status"] == "failed").sum()))
completed = df[df["status"] == "completed"]
avg_latency = int(completed["latency_ms"].mean()) if not completed.empty else 0
col4.metric("Avg latency (ms)", avg_latency)

st.subheader("Findings by category")
category_totals = {}
for row in df["category_counts"].dropna():
    for category, count in (row or {}).items():
        category_totals[category] = category_totals.get(category, 0) + count
if category_totals:
    st.bar_chart(pd.Series(category_totals, name="count"))
else:
    st.caption("No findings logged yet.")

st.subheader("Findings per run over time")
timeline = df.set_index("created_at").sort_index()
st.line_chart(timeline["findings_count"])

st.subheader("Recent runs")
st.dataframe(
    df[
        [
            "created_at",
            "repo",
            "pr_number",
            "status",
            "findings_count",
            "latency_ms",
            "model",
            "error",
        ]
    ],
    use_container_width=True,
)
