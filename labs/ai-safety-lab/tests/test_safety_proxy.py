import pytest
from fastapi.testclient import TestClient
from app.safety_proxy import app, detect_pii

client = TestClient(app)

def test_detect_pii_logic():
    # Presidio/Regex detection
    assert detect_pii("Contact Sample Patient A at 555-123-4567") == True
    assert detect_pii("My SSN is 123-45-6789") == True
    assert detect_pii("Safe summary of patient health.") == False

def test_middleware_pii_blocking(monkeypatch):
    """Test that the Middleware blocks response if LLM returns PII."""
    async def mock_call_llm(prompt):
        return '{"summary": "Patient Sample Patient A has SSN 123-45-6789", "risk_level": 2, "recommended_action": "None"}'
    
    monkeypatch.setattr("app.safety_proxy.call_llm", mock_call_llm)
    
    response = client.post("/analyze", json={"patient_data": "some data"})
    assert response.status_code == 502
    assert "PII Detected" in response.json()["detail"]

def test_middleware_schema_blocking(monkeypatch):
    """Test that the Middleware blocks response if LLM returns invalid schema."""
    async def mock_call_llm(prompt):
        # Missing recommended_action
        return '{"summary": "Valid summary", "risk_level": 1}'
    
    monkeypatch.setattr("app.safety_proxy.call_llm", mock_call_llm)
    
    response = client.post("/analyze", json={"patient_data": "some data"})
    assert response.status_code == 502
    assert "Invalid Schema Output" in response.json()["detail"]

def test_circuit_breaker_tripping(monkeypatch):
    """Test that the system falls back to a dumb template after failures."""
    import httpx
    
    async def mock_call_llm_fail(prompt):
        raise httpx.HTTPError("Connection failed")
    
    monkeypatch.setattr("app.safety_proxy.call_llm", mock_call_llm_fail)
    
    # Trigger 3 failures
    for _ in range(3):
        client.post("/analyze", json={"patient_data": "some data"})
        
    # 4th call should hit circuit breaker immediately
    response = client.post("/analyze", json={"patient_data": "some data"})
    assert response.status_code == 200
    assert "Circuit Breaker Active" in response.json()["summary"]
