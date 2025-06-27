import random
from datetime import datetime
from faker import Faker
from common.generator import create_generator_app

# Initialize Faker for generating realistic fake data
fake = Faker()

# Define Kafka topics specific to this generator
TOPIC_RAW = "raw_financial_events"
TOPIC_MALFORMED = "malformed_financial_events"

def generate_valid_payload():
    """Generates a single, valid financial transaction payload."""
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

# Create the Flask app using the common factory function
app = create_generator_app(
    generator_name='financial_generator',
    topic_raw=TOPIC_RAW,
    topic_malformed=TOPIC_MALFORMED,
    generate_valid_payload_func=generate_valid_payload
)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
