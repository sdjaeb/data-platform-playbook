import threading
import time
import random
import os
import json
from datetime import datetime
from flask import Flask
from kafka import KafkaProducer
from faker import Faker

fake = Faker()
app = Flask(__name__)
running = False
producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BROKER", "kafka:29092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

GENERATOR = "financial-generator"

if GENERATOR == "financial-generator":
    TOPIC_RAW = "raw_financial_events"
    TOPIC_MALFORMED = "malformed_financial_events"
    def generate_valid():
        return {
            "transaction_id": f"FT-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "account_id": f"ACC-{random.randint(100,999)}",
            "amount": round(random.uniform(10, 1000), 2),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "transaction_type": random.choice(["debit", "credit"]),
            "merchant_id": f"MER-{fake.lexify(text='???')}",
            "category": random.choice(["groceries", "electronics", "travel"])
        }
elif GENERATOR == "insurance-generator":
    TOPIC_RAW = "raw_insurance_claims"
    TOPIC_MALFORMED = "malformed_insurance_claims"
    def generate_valid():
        return {
            "claim_id": f"IC-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "policy_number": f"POL-{random.randint(100000,999999)}",
            "claim_amount": round(random.uniform(100, 10000), 2),
            "claim_type": random.choice(["auto", "home", "health"]),
            "claim_status": random.choice(["submitted", "approved", "rejected"]),
            "customer_id": f"CUST-{fake.lexify(text='???')}",
            "incident_date": datetime.utcnow().isoformat() + "Z"
        }
elif GENERATOR == "sports-generator":
    TOPIC_RAW = "raw_sports_events"
    TOPIC_MALFORMED = "malformed_sports_events"
    def generate_valid():
        return {
            "event_id": f"SE-{random.randint(1000,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sport": random.choice(["soccer", "basketball", "tennis"]),
            "team_a": fake.company(),
            "team_b": fake.company(),
            "score_a": random.randint(0, 5),
            "score_b": random.randint(0, 5),
            "location": fake.city(),
            "status": random.choice(["scheduled", "in_progress", "finished"])
        }
else:
    raise Exception("Unknown generator type")

def generate_data():
    global running
    while running:
        msg = generate_valid()
        producer.send(TOPIC_RAW, msg)
        print(f"Sent: {msg}")
        time.sleep(1)

@app.route('/start')
def start():
    global running
    if not running:
        running = True
        threading.Thread(target=generate_data, daemon=True).start()
    return "Started"

@app.route('/stop')
def stop():
    global running
    running = False
    return "Stopped"

@app.route('/malformed')
def malformed():
    count = random.randint(1, 10)
    for _ in range(count):
        bad_msg = {"bad_field": "malformed_data", "timestamp": datetime.utcnow().isoformat() + "Z"}
        producer.send(TOPIC_MALFORMED, bad_msg)
        print(f"Sent malformed: {bad_msg}")
    return f"Sent {count} malformed messages"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
