# Real-Time Stock Market Data Pipeline

A production-grade streaming data pipeline that ingests live stock prices, processes them in real-time, stores results in a relational database, and visualizes them on a live dashboard.

---

## Architecture

```
Stock API (yfinance)
      │
      ▼
┌─────────────┐
│   Kafka     │  ← Message broker / buffer
│ stock-prices│     Topic: "stock-prices"
└─────────────┘
      │
      ▼
┌─────────────┐
│    Spark    │  ← Stream processor (micro-batch, 10s windows)
│  Structured │     Aggregates avg & latest price per symbol
│  Streaming  │
└─────────────┘
      │
      ▼
┌─────────────┐
│ PostgreSQL  │  ← Persistent storage
│  stockdb    │     Table: stock_prices
└─────────────┘
      │
      ▼
┌─────────────┐
│  Streamlit  │  ← Live dashboard (auto-refreshes every 30s)
│  Dashboard  │     Price cards + historical line charts
└─────────────┘
```

All components run in Docker containers and communicate over an internal Docker network.

---

## Tech Stack

| Tool | Role | Why |
|---|---|---|
| **Apache Kafka** | Message streaming | Decouples producer from consumer; buffers messages if Spark goes down |
| **Apache Spark** | Stream processing | Micro-batch aggregations with fault tolerance and offset tracking |
| **PostgreSQL** | Storage | Queryable history of price snapshots over time |
| **Streamlit** | Dashboard | Pure Python, interactive, easy to extend |
| **Docker Compose** | Orchestration | Runs all services locally with a single command |
| **yfinance** | Data source | Free real-time stock price API, no key required |

---

## Project Structure

```
stock-pipeline/
├── docker-compose.yml          # All services defined here
├── kafka/
│   └── create-topics.sh        # Auto-creates Kafka topic on startup
├── producer/
│   ├── producer.py             # Fetches stock prices → publishes to Kafka
│   └── requirements.txt
├── spark/
│   ├── spark_processor.py      # Reads Kafka → aggregates → writes to PostgreSQL
│   └── postgresql-42.6.0.jar  # JDBC driver for PostgreSQL
├── postgres/
│   └── init.sql                # Creates stock_prices table on first run
└── dashboard/
    ├── app.py                  # Streamlit dashboard
    └── requirements.txt
```

---

## Getting Started

### Prerequisites
- Docker Desktop installed and running
- Python 3.9+ with pip
- Git Bash (recommended on Windows)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd stock-pipeline
```

### 2. Start all infrastructure

```bash
docker-compose up -d
```

This starts Zookeeper, Kafka, Spark, PostgreSQL, and the Streamlit dashboard. The `kafka-setup` service automatically creates the `stock-prices` topic.

### 3. Start the producer

```bash
cd producer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python producer.py
```

You should see stock prices being sent to Kafka every 10 seconds:
```
Sent: {'symbol': 'AAPL', 'price': 253.79, 'timestamp': '2026-04-01T10:30:07'}
Sent: {'symbol': 'GOOGL', 'price': 287.56, 'timestamp': '2026-04-01T10:30:07'}
Sent: {'symbol': 'MSFT', 'price': 370.17, 'timestamp': '2026-04-01T10:30:08'}
```

### 4. View the dashboard

Open your browser at:
```
http://localhost:8501
```

---

## How It Works

### Producer
The Python producer uses `yfinance` to fetch the latest price for each stock symbol every 10 seconds. Each price update is serialized as JSON and published to the Kafka topic `stock-prices`.

### Kafka
Kafka acts as a buffer between the producer and Spark. If Spark goes down, messages queue up and are replayed when it restarts — no data loss. Each message is assigned an **offset** so consumers can track exactly where they left off.

### Spark Structured Streaming
Spark reads from Kafka in micro-batches every 10 seconds. For each batch it:
1. Parses the JSON message
2. Groups by stock symbol
3. Calculates the average and latest price
4. Writes results to PostgreSQL via JDBC

### PostgreSQL
Stores a time-series of price snapshots. Each row represents one symbol's aggregated price at a point in time, building up a queryable history.

### Streamlit Dashboard
Reads directly from PostgreSQL and displays:
- **Current price cards** for each symbol with average price delta
- **Line charts** showing price history over time
- Auto-refreshes every 30 seconds

---

## Tracked Stocks

| Symbol | Company |
|---|---|
| AAPL | Apple Inc. |
| GOOGL | Alphabet Inc. |
| MSFT | Microsoft Corporation |

To add more stocks, update `STOCKS` in `producer/producer.py`:
```python
STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA"]
```

---

## Key Engineering Decisions

**Why Kafka instead of calling Spark directly?**
Kafka decouples the producer from the consumer. If Spark restarts, Kafka replays missed messages from the last committed offset. Without Kafka, any downtime means lost data.

**Why Spark instead of plain Python?**
Spark provides built-in fault tolerance, offset management, and micro-batch windowing. It's also horizontally scalable — the same code runs on a laptop or a 100-node cluster.

**Why micro-batch instead of pure streaming?**
Spark Structured Streaming uses micro-batches (processing windows) rather than processing every message individually. This gives near real-time latency (seconds) with much better throughput and easier aggregation semantics.

**Why Docker Compose?**
All services — Kafka, Zookeeper, Spark, PostgreSQL, Streamlit — run in isolated containers with a single `docker-compose up -d`. No local installation of Java, Scala, or Kafka required.

---

## Sample Data

```sql
SELECT * FROM stock_prices ORDER BY processed_at DESC LIMIT 5;

 id | symbol | avg_price | latest_price |        processed_at
----+--------+-----------+--------------+----------------------------
 42 | MSFT   |    370.17 |       370.17 | 2026-04-01 10:44:25.826575
 41 | GOOGL  |    287.56 |       287.56 | 2026-04-01 10:44:24.701237
 40 | AAPL   |    253.79 |       253.79 | 2026-04-01 10:44:23.601412
```

---

## Future Improvements

- Add **Apache Airflow** for pipeline orchestration and health monitoring
- Add **more stock symbols** and sector grouping
- Implement **price change alerts** when a stock moves more than X%
- Add **candlestick charts** for OHLC data
- Deploy to **AWS/GCP** using managed Kafka (MSK) and Spark (EMR/Dataproc)
- Add **data quality checks** using Great Expectations

---

## Skills Demonstrated

- **Stream processing** with Apache Kafka and Spark Structured Streaming
- **Containerization** with Docker and Docker Compose
- **Data modeling** with PostgreSQL
- **Pipeline design** — decoupled, fault-tolerant, scalable architecture
- **Python** — producer, PySpark, Streamlit dashboard
- **Real-world debugging** — Kafka listeners, JDBC drivers, Docker networking