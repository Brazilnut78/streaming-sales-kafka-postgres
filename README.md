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
