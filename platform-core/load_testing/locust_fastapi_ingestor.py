# Description: Locust load test script for the FastAPI Data Ingestor.
# Source: Deep-Dive Addendum: IaC & CI/CD Recipes, Section 5.4.
#
# This script defines two tasks to simulate traffic:
# 1. ingest_financial_transaction: Sends mock financial transaction data.
# 2. ingest_insurance_claim: Sends mock insurance claim data.
#
# The user can configure the host, number of users, and spawn rate via the Locust UI
# (usually http://localhost:8089 after running `locust -f locust_fastapi_ingestor.py`).
from locust import HttpUser, task, between
import json
from datetime import datetime, timedelta
import random

class FinancialDataUser(HttpUser):
    """
    User class that simulates sending financial and insurance data to the FastAPI ingestor.
    """
    # Wait time between requests for each simulated user.
    # This helps simulate more realistic user behavior rather than hammering the API constantly.
    wait_time = between(0.1, 0.5) # Simulate delay between requests (0.1 to 0.5 seconds)

    # The host URL for the FastAPI application. This should match the exposed port in docker-compose.
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
            "category": random.choice(["groceries", "utilities", "salary", "entertainment", "transport", "housing", "healthcare", "education"]),
            "is_flagged": random.choice([True, False]) # Add the new field for consistency
        }
        # Send the POST request. The 'name' parameter helps in grouping statistics in Locust UI.
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
            "claim_amount": round(random.uniform(500.0, 50000.0), 2),
            "claim_type": random.choice(["auto", "health", "home", "life", "property"]),
            "claim_status": random.choice(["submitted", "under_review", "approved", "rejected", "closed"]),
            "customer_id": f"CUST-{random.randint(10000, 99999)}",
            "incident_date": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat() # Incident in past year
        }
        self.client.post("/ingest-insurance-claim/", json=claim_data, name="/ingest-insurance-claim")
