import threading
import time
import random
import os
import json
from datetime import datetime
from flask import Flask
from kafka import KafkaProducer

# Use a thread-safe way to manage the 'running' state.
# A simple dictionary is used for this mutable state.
_state = {'running': False}

def create_generator_app(generator_name, topic_raw, topic_malformed, generate_valid_payload_func):
    """
    Creates a standard Flask application for a data generator.

    Args:
        generator_name (str): The name of the Flask application.
        topic_raw (str): The Kafka topic for valid, raw data.
        topic_malformed (str): The Kafka topic for malformed data.
        generate_valid_payload_func (function): A function that returns a dictionary
                                                representing a valid data payload.

    Returns:
        Flask: A configured Flask application instance.
    """
    app = Flask(generator_name)
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BROKER", "kafka:29092"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    def _generate_data_loop():
        """The loop that continuously generates and sends data."""
        while _state.get('running', False):
            msg = generate_valid_payload_func()
            producer.send(topic_raw, msg)
            print(f"Sent: {msg}")
            time.sleep(1)

    @app.route('/start')
    def start():
        """Starts the data generation thread."""
        if not _state['running']:
            _state['running'] = True
            threading.Thread(target=_generate_data_loop, daemon=True).start()
            print(f"'{generator_name}' started.")
        return "Started"

    @app.route('/stop')
    def stop():
        """Stops the data generation thread."""
        _state['running'] = False
        print(f"'{generator_name}' stopped.")
        return "Stopped"

    @app.route('/malformed')
    def malformed():
        """Sends a random number of malformed messages to the malformed topic."""
        count = random.randint(1, 10)
        for _ in range(count):
            bad_msg = {
                "bad_field": "malformed_data",
                "error_description": "Intentional malformed event for testing.",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            producer.send(topic_malformed, bad_msg)
            print(f"Sent malformed: {bad_msg}")
        return f"Sent {count} malformed messages"

    return app