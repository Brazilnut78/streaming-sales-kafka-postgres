import json, time, uuid, random, datetime as dt
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "sales"
RATE_PER_SEC = 1   # <- change to 3 for three sales per second

p = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

channels = ["web", "in_store", "call_center", "marketplace"]

def make_sale():
    payload = {
        "id": str(uuid.uuid4()),
        "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "store_id": random.randint(100, 199),
        "amount_usd": round(random.uniform(5, 250), 2),
        "channel": random.choice(channels),
    }
    return payload

def delivery(err, msg):
    if err:
        print(f"❌ delivery failed: {err}")
    else:
        pass  # delivered OK

interval = 1.0 / RATE_PER_SEC
print(f"Producing to '{TOPIC}' at ~{RATE_PER_SEC}/sec. Ctrl+C to stop.")
try:
    while True:
        sale = make_sale()
        p.produce(TOPIC, json.dumps(sale).encode("utf-8"), callback=delivery)
        p.poll(0)   # serve delivery callbacks
        time.sleep(interval)
except KeyboardInterrupt:
    print("\nStopping producer…")
finally:
    p.flush(10)
