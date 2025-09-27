# Streaming Sales: Kafka → PostgreSQL (Python)

Tiny streaming demo: a Python Kafka **producer** generates mock sales events; a Python **consumer** inserts them into PostgreSQL. Includes quick setup, retention tips, and SQL checks.

## Prereqs
- Python 3.10+
- Kafka running locally (`localhost:9092`) with topic `sales`
- PostgreSQL running locally (defaults to DB `dvdrental`)

## Install
```bat
py -m pip install -r requirements.txt
