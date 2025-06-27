import random
from datetime import datetime
from faker import Faker
from common.generator import create_generator_app

# Initialize Faker for generating realistic fake data
fake = Faker()

# Define Kafka topics specific to this generator
TOPIC_RAW = "raw_insurance_claims"
TOPIC_MALFORMED = "malformed_insurance_claims"

def generate_valid_payload():
    """Generates a single, valid insurance claim payload."""
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

# Create the Flask app using the common factory function
app = create_generator_app(
    generator_name='insurance_generator',
    topic_raw=TOPIC_RAW,
    topic_malformed=TOPIC_MALFORMED,
    generate_valid_payload_func=generate_valid_payload
)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
