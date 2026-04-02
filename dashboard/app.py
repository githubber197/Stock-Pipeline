import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import create_engine
import time

#Config
DB_URL = "postgresql://stockuser:stockpass@postgres:5432/stockdb"

def get_engine():
    return create_engine(DB_URL)

def fetch_stock_data():
    query = """
        SELECT symbol, avg_price, latest_price, processed_at
        FROM stock_prices
        ORDER BY processed_at DESC
        LIMIT 300
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn)
    return df

#Page config
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Real-Time Stock Market Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

#Fetch data from PostgreSQL
df = fetch_stock_data()

if df.empty:
    st.warning("No data yet. Make sure your producer and Spark job are running.")
else:
    st.subheader("Current Prices")
    latest = df.groupby("symbol").first().reset_index()

    cols = st.columns(len(latest))
    for i, row in latest.iterrows():
        with cols[i]:
            st.metric(
                label=row["symbol"],
                value=f"${row['latest_price']:.2f}",
                delta=f"avg ${row['avg_price']:.2f}"
            )

    st.divider()

    st.subheader("Price History")
    for symbol in df["symbol"].unique():
        symbol_df = df[df["symbol"] == symbol].sort_values("processed_at")
        fig = px.line(
            symbol_df,
            x="processed_at",
            y="latest_price",
            title=f"{symbol} Price Over Time",
            labels={"latest_price": "Price ($)", "processed_at": "Time"}
        )
        st.plotly_chart(fig, width="stretch")

st.markdown("---")
st.caption("Dashboard auto-refreshes every 30 seconds")

#Streamlit refresh
time.sleep(30)
st.rerun()