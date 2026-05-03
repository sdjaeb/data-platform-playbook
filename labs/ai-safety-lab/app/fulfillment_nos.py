import os
import json
import logging
from typing import Annotated, Dict, List, TypedDict, Union, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fulfillment-nos")

app = FastAPI(title="FulfillmentAI NOS Intelligence Layer")

# --- 1. The Schema (Supply Chain Visibility) ---
class RoutingRecommendation(BaseModel):
    order_id: str
    selected_warehouse: str
    estimated_cost: float
    shipping_method: str
    logic_reasoning: str = Field(description="The LLM's explanation for this route")

class AgentState(TypedDict):
    order_data: Dict[str, Any]
    inventory_snapshot: Dict[str, int]
    recommendation: Optional[RoutingRecommendation]
    safety_violations: List[str]
    retries: int

# --- 2. Mock Logistics Data (The "Intelligence Layer") ---
MOCK_INVENTORY = {
    "WH-ATL-01": 500,  # Atlanta
    "WH-LAX-02": 0,    # Los Angeles (OUT OF STOCK)
    "WH-ORD-03": 120,  # Chicago
    "WH-OVERSEAS-99": 1000 # High cost
}

# --- 3. The LangGraph Nodes ---

async def analyze_routing(state: AgentState):
    """LLM Node: Proposes a routing solution."""
    order = state["order_data"]
    inventory = state["inventory_snapshot"]
    
    # MOCKING LLM response
    if state.get("retries", 0) == 0:
        return {
            "recommendation": RoutingRecommendation(
                order_id=order["id"],
                selected_warehouse="WH-LAX-02", 
                estimated_cost=12.50,
                shipping_method="Ground",
                logic_reasoning="Closest to customer zip 90210"
            ),
            "retries": 1
        }
    else:
        return {
            "recommendation": RoutingRecommendation(
                order_id=order["id"],
                selected_warehouse="WH-ORD-03",
                estimated_cost=22.50,
                shipping_method="Air",
                logic_reasoning="Only warehouse with sufficient stock."
            )
        }

def safety_audit(state: AgentState):
    """Safety Node: Validates the LLM's recommendation against ground truth."""
    violations = []
    rec = state["recommendation"]
    inventory = state["inventory_snapshot"]
    
    if not rec:
        return {"safety_violations": ["No recommendation generated"]}

    # Rule 1: Inventory Check
    stock = inventory.get(rec.selected_warehouse, 0)
    if stock <= 0:
        violations.append(f"INVENTORY_ERROR: {rec.selected_warehouse} is out of stock.")
    
    # Rule 2: Financial Guardrail
    if rec.estimated_cost > 1000:
        violations.append("FINANCIAL_ERROR: Shipping cost exceeds threshold.")

    return {"safety_violations": violations}

def should_continue(state: AgentState):
    """Conditional Edge: Decides if we need to loop back or finish."""
    if state.get("safety_violations"):
        if state.get("retries", 0) >= 3:
            return "end" 
        return "retry"
    return "end"

def get_nos_executor():
    # We use a wrapper to ensure monkeypatching works during tests
    import app.fulfillment_nos as nos
    workflow = StateGraph(AgentState)
    workflow.add_node("analyze", nos.analyze_routing)
    workflow.add_node("audit", nos.safety_audit)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "audit")
    workflow.add_conditional_edges("audit", nos.should_continue, {"retry": "analyze", "end": END})
    return workflow.compile()

# --- 5. API Endpoints ---
@app.post("/nos/optimize")
async def optimize_route(order: Dict[str, Any]):
    initial_state = {
        "order_data": order,
        "inventory_snapshot": MOCK_INVENTORY,
        "recommendation": None,
        "safety_violations": [],
        "retries": 0
    }
    
    executor = get_nos_executor()
    result = await executor.ainvoke(initial_state)
    
    if result["safety_violations"]:
        logger.error(f"Routing Failed Safety Audit: {result['safety_violations']}")
        raise HTTPException(status_code=502, detail=f"Safety Violation: {result['safety_violations']}")
    
    return result["recommendation"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
