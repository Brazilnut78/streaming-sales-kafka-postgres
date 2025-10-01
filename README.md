## 📖 Overview

A lightweight streaming demo you can run on your laptop:  
- A **Python Kafka producer** generates mock sales events.  
- A **Python consumer** writes them into PostgreSQL.  
- Includes quick setup, topic retention tweaks, and simple SQL checks.  
- The consumer commits offsets **only after a successful DB insert** and uses  
  `ON CONFLICT DO NOTHING` for idempotent upserts (guaranteeing exactly-once per ID).
- A Streamlit dashboard visualizes the results.

## ❓ Why this project?

- Simulates a real-time API “firehose” **without paid cloud services or extra costs**.  
- Lets you practice the **essentials of streaming systems**: topics, partitions, consumer groups, offsets, idempotent upserts, and retention.  
- Analyze results instantly in SQL and build intuition for **lag, throughput, and backpressure** — all on a local machine.  

### Prereqs
- **Python** 3.10+ (Windows/macOS/Linux)
- **Kafka** 3.x/4.x running locally on `localhost:9092`  
  - Topic: `sales` (create with `kafka-topics --create --topic sales --partitions 3 --replication-factor 1`)
- **PostgreSQL** 14+ running locally (defaults in repo use DB `dvdrental`)
  - pgAdmin or `psql` for quick checks
- Pip packages (see requirements files below)

Install Dependencies:
>
There are 2 sets of deps:
>
> ```bash
> # For the Streamlit Dashboard (cloud or local)
> pip install -r requirements.streamlitapp.txt
>
> # For the local Kafka → Postgres pipeline
> pip install -r requirements-pipeline.txt
>

(Optional) keep Kafka small (1-day retention):**
> ```bat
> cd C:\kafka\kafka_2.13-4.1.0
> bin\windows\kafka-configs.bat --bootstrap-server localhost:9092 --entity-type topics --entity-name sales --alter --add-config retention.ms=86400000
> ```

---

## 🏗️ Architecture (at a glance)

1. **producer.py** → generates mock sales events  
2. **Kafka (topic: `sales`)** → stores events across partitions (`sales-0`, `sales-1`, …)  
3. **consumer_to_pg.py** → consumes events from Kafka and inserts into Postgres  
4. **PostgreSQL (table: `sales_events`)** → persists events for SQL queries  



**JSON events:** `{ id, ts, store_id, amount_usd, channel }`

---

## 🚀 Quick Start

### Step 1: Start the Kafka Broker (must be running)

From your Kafka install folder, start ZooKeeper and the Kafka broker:

    cd C:\kafka\kafka_2.13-4.1.0
    bin\windows\zookeeper-server-start.bat config\zookeeper.properties
    bin\windows\kafka-server-start.bat config\server.properties

> ⚠️ Note: ZooKeeper is only required for older Kafka versions (pre–3.3).  
> Modern Kafka releases (KRaft mode) no longer need ZooKeeper, since Kafka now manages its own metadata and cluster coordination.  
> If you are using Kafka 3.3+ in KRaft mode, you can skip the ZooKeeper step and just start the broker.

### Step 2: Create the Kafka Topic (one-time only)
Create the sales topic with 3 partitions:

    cd C:\kafka\kafka_2.13-4.1.0
    bin\windows\kafka-topics.bat --bootstrap-server localhost:9092 ^
      --create --topic sales --partitions 3 --replication-factor 1

### Step 3: Start Producing Mock Sales
Stream 3 sales per second into the sales topic:

    python producer.py --bootstrap-server localhost:9092 --topic sales --sales-per-second 3

### Step 4: Start the Consumer (Write to Postgres)
Consume messages and persist them into Postgres:

    python consumer_to_pg.py

### Step 5: Verify in SQL
Check the latest rows directly in Postgres:

    SELECT COUNT(*) AS rows, MAX(ts) AS latest_ts FROM public.sales_events;
    SELECT * FROM public.sales_events ORDER BY ts DESC LIMIT 10;

## 📊 Streamlit Dashboard

This repository now includes a live dashboard built with Streamlit.

### Run the Dashboard

Run the following commands to install dependencies and start the dashboard:

```bash
pip install -r requirements.txt && streamlit run Dashboard_Live_Sales.py



    
