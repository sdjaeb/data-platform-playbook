import random
from datetime import datetime
from faker import Faker
from common.generator import create_generator_app

# Initialize Faker for generating realistic fake data
fake = Faker()

# Define Kafka topics specific to this generator
TOPIC_RAW = "raw_sports_events"
TOPIC_MALFORMED = "malformed_sports_events"

def generate_valid_payload():
    """Generates a single, valid sports event payload."""
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

# Create the Flask app using the common factory function
app = create_generator_app(
    generator_name='sports_generator',
    topic_raw=TOPIC_RAW,
    topic_malformed=TOPIC_MALFORMED,
    generate_valid_payload_func=generate_valid_payload
)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)
