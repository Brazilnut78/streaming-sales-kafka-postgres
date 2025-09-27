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
+-------------+         Kafka (topic: sales)         +------------------+
| producer.py |  -->  [ sales-0 | sales-1 | ... ] -> | consumer_to_pg.py | -> PostgreSQL (sales_events)
+-------------+                                       +------------------+
     JSON events: {id, ts, store_id, amount_usd, channel}

Quick start
1) Create the topic (one time)

Windows (Kafka for Windows):

cd C:\kafka\kafka_2.13-4.1.0
bin\windows\kafka-topics.bat --bootstrap-server localhost:9092 --create --topic sales --partitions 3 --replication-factor 1


macOS/Linux:

kafka-topics --bootstrap-server localhost:9092 --create --topic sales --partitions 3 --replication-factor 1

2) Run the producer
py producer.py --bootstrap localhost:9092 --topic sales --rate 1

3) Run the consumer (writes to Postgres)

Replace the password before running (see “Passwords & Safety” below).

py consumer_to_pg.py

4) Verify in SQL
SELECT COUNT(*) AS rows, MAX(ts) AS latest_ts FROM public.sales_events;
SELECT * FROM public.sales_events ORDER BY ts DESC LIMIT 10;

Create the table (if you need to do it manually)
CREATE TABLE IF NOT EXISTS public.sales_events (
  id         UUID PRIMARY KEY,
  ts         TIMESTAMPTZ NOT NULL,
  store_id   INT NOT NULL,
  amount_usd NUMERIC(10,2) NOT NULL,
  channel    TEXT NOT NULL
);

Keep Kafka from filling disk

Keep last 1 day of data:

cd C:\kafka\kafka_2.13-4.1.0
bin\windows\kafka-configs.bat --bootstrap-server localhost:9092 --entity-type topics --entity-name sales --alter --add-config retention.ms=86400000


Optionally also cap size (~50 MB):

bin\windows\kafka-configs.bat --bootstrap-server localhost:9092 --entity-type topics --entity-name sales --alter --add-config retention.bytes=52428800


Check settings:

bin\windows\kafka-configs.bat --bootstrap-server localhost:9092 --entity-type topics --entity-name sales --describe

Useful SQL snippets

Last 5 minutes by channel

SELECT channel,
       COUNT(*) AS events,
       ROUND(SUM(amount_usd), 2) AS revenue
FROM public.sales_events
WHERE ts >= now() - interval '5 minutes'
GROUP BY channel
ORDER BY revenue DESC;


Table & DB size

SELECT pg_size_pretty(pg_total_relation_size('public.sales_events')) AS table_size;
SELECT pg_size_pretty(pg_database_size('dvdrental')) AS db_size;

Passwords & safety

In consumer_to_pg.py, the password is a placeholder (CHANGE_ME).

Option A (simple): edit it locally before running—do not commit real passwords.

Option B (safer): read from an environment variable instead. Example change:

import os
PG["password"] = os.getenv("PGPASSWORD") or "CHANGE_ME"


Run with:

set PGPASSWORD=YourPassword
py consumer_to_pg.py


If you ever commit a real password, rotate it in Postgres immediately:

ALTER ROLE postgres WITH PASSWORD 'NewStrongPassword!';

Monitoring & troubleshooting

Is the consumer running?

cd C:\kafka\kafka_2.13-4.1.0
bin\windows\kafka-consumer-groups.bat --bootstrap-server localhost:9092 --group sales-to-pg --describe


If it says no active members, the consumer isn’t running.

LAG dropping toward 0 = healthy consumption.

Common fixes

relation "public.sales_events" does not exist → run the CREATE TABLE in the correct database.

password authentication failed → wrong credentials; reset or update.

No rows in SQL but console consumer shows data → your Python consumer isn’t running or points to the wrong dbname/port.

pip not recognized → use py -m pip install -r requirements.txt.

Cleanup (optional)

Keep only 30 days in Postgres:

DELETE FROM public.sales_events WHERE ts < now() - interval '30 days';
VACUUM (ANALYZE) public.sales_events;


Schedule the query with Windows Task Scheduler or use pgAgent if you want it automated.
