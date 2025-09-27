import json, psycopg2, psycopg2.extras, time
from confluent_kafka import Consumer

# ---- Kafka ----
KAFKA_CONFIG = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "sales-to-pg",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
}
TOPIC = "sales"

# ---- Postgres (EDIT THESE) ----
PG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "dvdrental",
    "user": "postgres",
    "password": "CHANGE_ME",
}

SQL_UPSERT = """
INSERT INTO public.sales_events (id, ts, store_id, amount_usd, channel)
VALUES (%(id)s, %(ts)s, %(store_id)s, %(amount_usd)s, %(channel)s)
ON CONFLICT (id) DO NOTHING;
"""

def main():
    # connect to Postgres
    conn = psycopg2.connect(**PG)
    conn.autocommit = False
    cur = conn.cursor()

    # start Kafka consumer
    c = Consumer(KAFKA_CONFIG)
    c.subscribe([TOPIC])
    print(f"Consuming from '{TOPIC}' and inserting into Postgres… Ctrl+C to stop.")

    try:
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Kafka error: {msg.error()}")
                continue

            try:
                rec = json.loads(msg.value())
                psycopg2.extras.execute_values(
                    cur, SQL_UPSERT.replace("VALUES (%(id)s, %(ts)s, %(store_id)s, %(amount_usd)s, %(channel)s)", "VALUES %s"),
                    [rec], template="(%(id)s, %(ts)s, %(store_id)s, %(amount_usd)s, %(channel)s)"
                )
                conn.commit()
                c.commit(msg)  # commit Kafka offset after DB commit
            except Exception as e:
                conn.rollback()
                print(f"DB insert failed: {e}\nPayload: {msg.value()}")

    except KeyboardInterrupt:
        print("\nStopping consumer…")
    finally:
        c.close()
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
