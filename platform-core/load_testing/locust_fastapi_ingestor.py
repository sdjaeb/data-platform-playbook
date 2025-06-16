# locust_fastapi_ingestor.py
# This script defines a Locust load test for the FastAPI Data Ingestor.
# It simulates concurrent users sending financial transactions and insurance claims
# to the API, allowing you to measure performance under load.

# To run this:
# 1. Ensure Locust is installed: `pip install locust`
# 2. Save this file as `locust_fastapi_ingestor.py` in your project root.
# 3. Start your Docker Compose environment: `docker compose up --build -d`
# 4. Run Locust: `locust -f locust_fastapi_ingestor.py`
# 5. Open your browser to `http://localhost:8089` (Locust UI)
# 6. Enter the Host (e.g., `http://localhost:8000`), number of users, and spawn rate.

from locust import HttpUser, task, between
import json
from datetime import datetime, timedelta
import random

class FinancialDataUser(HttpUser):
    """
    User class that simulates sending financial and insurance data to the FastAPI ingestor.
    """
    # Define the time a user will wait between consecutive tasks.
    # This helps simulate more realistic user behavior rather than hammering the API constantly.
    wait_time = between(0.1, 0.5) # Simulate a delay between 0.1 and 0.5 seconds

    # The host URL for the FastAPI application.
    # This should match the exposed port in your docker-compose.yml for fastapi_ingestor.
    # In a local Docker Compose setup, FastAPI is often exposed on localhost:8000.
    host = "http://localhost:8000" # Target FastAPI endpoint

    @task(1) # This task has a weight of 1, meaning it will be executed proportionally to other tasks.
    def ingest_financial_transaction(self):
        """
        Simulates sending a financial transaction POST request to the FastAPI ingestor.
        Generates realistic-looking mock data for a financial transaction.
        """
        transaction_data = {
            "transaction_id": f"FT-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{random.randint(1000, 9999)}",
            "timestamp": datetime.now().isoformat(),
            "account_id": f"ACC-{random.randint(100000, 999999)}",
            "amount": round(random.uniform(1.0, 10000.0), 2), # Random amount between 1.00 and 10000.00
            "currency": random.choice(["USD", "EUR", "GBP", "JPY"]), # Random currency
            "transaction_type": random.choice(["debit", "credit", "transfer", "payment"]), # Random type
            "merchant_id": f"MER-{random.randint(100, 999)}" if random.random() > 0.3 else None, # Optional merchant ID
            "category": random.choice(["groceries", "utilities", "salary", "entertainment", "transport", "housing", "healthcare", "education"])
        }
        # Send the POST request. The 'name' argument groups requests in Locust's statistics.
        self.client.post("/ingest-financial-transaction/", json=transaction_data, name="/ingest-financial-transaction")

    @task(1) # This task also has a weight of 1.
    def ingest_insurance_claim(self):
        """
        Simulates sending an insurance claim POST request to the FastAPI ingestor.
        Generates realistic-looking mock data for an insurance claim.
        """
        claim_data = {
            "claim_id": f"IC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{random.randint(1000, 9999)}",
            "timestamp": datetime.now().isoformat(),
            "policy_number": f"POL-{random.randint(1000000, 9999999)}",
            "claim_amount": round(random.uniform(500.0, 50000.0), 2), # Random amount
            "claim_type": random.choice(["auto", "health", "home", "life", "property"]), # Random claim type
            "claim_status": random.choice(["submitted", "under_review", "approved", "rejected", "paid"]), # Random status
            "customer_id": f"CUST-{random.randint(10000, 99999)}",
            "incident_date": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat() # Incident date within last year
        }
        # Send the POST request.
        self.client.post("/ingest-insurance-claim/", json=claim_data, name="/ingest-insurance-claim")
