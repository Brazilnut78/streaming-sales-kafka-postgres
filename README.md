Tiny streaming demo: a Python Kafka **producer** generates mock sales events; a Python **consumer** inserts them into PostgreSQL. 
Includes quick setup, topic retention tips, and SQL checks. The consumer commits Kafka offsets **after** a successful DB insert 
and uses `ON CONFLICT DO NOTHING` for idempotent upserts (exactly-once per `id`).

### Prereqs
- **Python** 3.10+ (Windows/macOS/Linux)
- **Kafka** 3.x/4.x running locally on `localhost:9092`  
  - Topic: `sales` (create with `kafka-topics --create --topic sales --partitions 3 --replication-factor 1`)
- **PostgreSQL** 14+ running locally (defaults in repo use DB `dvdrental`)
  - pgAdmin or `psql` for quick checks
- **Pip packages**: `confluent-kafka`, `psycopg2-binary`
- **Terminal**: Command Prompt/PowerShell on Windows, Terminal on macOS/Linux

> Install deps:
> ```bat
> py -m pip install -r requirements.txt
> ```

> (Optional) keep Kafka small (1-day retention):
> ```bat
> cd C:\kafka\kafka_2.13-4.1.0
> bin\windows\kafka-configs.bat --bootstrap-server localhost:9092 --entity-type topics --entity-name sales --alter --add-config retention.ms=86400000
> ```

> Quick SQL checks:
> ```sql
> SELECT COUNT(*) AS rows, MAX(ts) AS latest_ts FROM public.sales_events;
> SELECT * FROM public.sales_events ORDER BY ts DESC LIMIT 10;
> ```

Why this project?

Simulates a real-time API “firehose” without paid services or cloud bills.

Practice the essentials of streaming systems on a laptop: topics, partitions, consumer groups, offsets, idempotent upserts, and retention.

Analyze results instantly in SQL and build intuition for lag, throughput, and backpressure.

Architecture (at a glance)
+-------------+     Kafka (topic: sales)     +------------------+
| producer.py | --> [ sales-0 | sales-1 | … ] --> | consumer_to_pg.py |
+-------------+                               +------------------+
                                                   |
                                                   v
                                       PostgreSQL (sales_events)

JSON events: { id, ts, store_id, amount_usd, channel }

🚀 Quick Start
📝 Step 1: Create the Kafka Topic (one-time only)

Windows (PowerShell / CMD):

cd C:\kafka\kafka_2.13-4.1.0
bin\windows\kafka-topics.bat --bootstrap-server localhost:9092 ^
  --create --topic sales --partitions 3 --replication-factor 1


macOS / Linux (bash):

kafka-topics.sh --bootstrap-server localhost:9092 \
  --create --topic sales --partitions 3 --replication-factor 1

📦 Step 2: Start Producing Mock Sales

Stream 3 sales per second into the sales topic:

python producer.py --bootstrap-server localhost:9092 --topic sales --sales-per-second 3

🗄️ Step 3: Start the Consumer (Write to Postgres)

Consume messages and persist them into Postgres:

python consumer_to_pg.py

🔍 Step 4: Verify in SQL

Check the latest rows directly in Postgres:

Quick SQL checks:

SELECT COUNT(*) AS rows, MAX(ts) AS latest_ts 
FROM public.sales_events;

SELECT * 
FROM public.sales_events 
ORDER BY ts DESC 
LIMIT 10;
