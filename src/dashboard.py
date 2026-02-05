import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Paths ---
SRC_DIR = Path(_file_).resolve().parent
BASE_DIR = SRC_DIR.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

APPS_FILE = PROCESSED_DIR / "apps_kpis.csv"
DAILY_FILE = PROCESSED_DIR / "daily_metrics.csv"

# --- Load data ---
apps_df = pd.read_csv(APPS_FILE)
daily_df = pd.read_csv(DAILY_FILE, parse_dates=['review_date'])

# --- Streamlit App ---
st.title("Lightweight App Reviews Dashboard")
st.write("A simple dashboard showing app-level KPIs and review trends over time.")

# --- Sidebar filters ---
top_n = st.sidebar.slider("Select top N apps by average rating", min_value=5, max_value=len(apps_df), value=10)

# --- 1. App Performance ---
st.header("App Performance: Average Rating")
top_apps = apps_df.sort_values('avg_rating', ascending=False).head(top_n)
fig_apps = px.bar(
    top_apps,
    x='avg_rating',
    y='app_name',
    orientation='h',
    text='avg_rating',
    color='avg_rating',
    color_continuous_scale='Viridis'
)
fig_apps.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title='Average Rating', yaxis_title='App Name')
st.plotly_chart(fig_apps, use_container_width=True)

# --- 2. Review Trends Over Time ---
st.header("Average Ratings Over Time")
fig_trend = px.line(
    daily_df,
    x='review_date',
    y='daily_avg_rating',
    markers=True,
    title='Average Rating Over Time'
)
fig_trend.update_layout(xaxis_title='Date', yaxis_title='Average Rating')
st.plotly_chart(fig_trend, use_container_width=True)

# --- 3. Daily Review Volume ---
st.header("Daily Review Volume")
fig_volume = px.bar(
    daily_df,
    x='review_date',
    y='daily_num_reviews',
    title='Number of Reviews Per Day'
)
fig_volume.update_layout(xaxis_title='Date', yaxis_title='Number of Reviews')
st.plotly_chart(fig_volume, use_container_width=True)

# --- Summary ---
st.markdown("""
### Dashboard Insights
- *Top apps by average rating*: Quickly see which apps perform best or worst.
- *Ratings over time*: Detect if user ratings are improving or declining.
- *Review volume*: Monitor engagement trends across days.
""")
