import pytest
from fastapi.testclient import TestClient
from app.fulfillment_nos import app, RoutingRecommendation

client = TestClient(app)

def test_nos_self_correction():
    order_data = {"id": "ORD-123"}
    response = client.post("/nos/optimize", json=order_data)
    assert response.status_code == 200
    assert response.json()["selected_warehouse"] == "WH-ORD-03"

def test_nos_fail_after_retries(monkeypatch):
    # Force the LLM node to always pick the out-of-stock warehouse
    async def mock_analyze_bad(state):
        return {
            "recommendation": RoutingRecommendation(
                order_id="ORD-BAD",
                selected_warehouse="WH-LAX-02",
                estimated_cost=10.0,
                shipping_method="Ground",
                logic_reasoning="Stubbornly picking LAX."
            ),
            "retries": state.get("retries", 0) + 1
        }
    
    # Patch the function in the module so get_nos_executor() picks it up
    monkeypatch.setattr("app.fulfillment_nos.analyze_routing", mock_analyze_bad)
    
    response = client.post("/nos/optimize", json={"id": "ORD-BAD"})
    assert response.status_code == 502
    assert "INVENTORY_ERROR" in response.json()["detail"]
