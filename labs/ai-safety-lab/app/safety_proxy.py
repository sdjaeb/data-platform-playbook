import json
import logging
import re
import uuid
from typing import Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from presidio_analyzer import AnalyzerEngine
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safety-proxy")

app = FastAPI(title="AI Safety & Governance Proxy")

# Initialize Presidio Analyzer
analyzer = AnalyzerEngine()

# --- 1. The "Harness" (Schema Definition) ---
class PatientAnalysis(BaseModel):
    summary: str
    risk_level: int
    recommended_action: str


class AnalysisRequest(BaseModel):
    patient_data: str
    sensitive_input_approved: bool = False

# --- 4. The "Orchestration" (State) ---
CIRCUIT_BREAKER_LIMIT = 3
failure_counter = 0

# --- 2. The "Risk Mitigation" (PII Scrubber) ---
def detect_pii(text: str) -> bool:
    """
    Uses Presidio and Regex to detect PII (SSN, Phone, Email, etc.)
    """
    # 1. Presidio Analysis
    results = analyzer.analyze(text=text, entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN", "PERSON"], language='en')
    if results:
        logger.warning(f"Presidio detected PII entities: {[r.entity_type for r in results]}")
        return True
    
    # 2. Regex Fallback for simulated SSN (XXX-XX-XXXX)
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    if re.search(ssn_pattern, text):
        logger.warning("Regex detected simulated SSN.")
        return True
        
    return False

# --- 1. The "Harness" (Guardrail Middleware) ---
@app.middleware("http")
async def safety_guardrail_middleware(request: Request, call_next):
    """
    Middleware that intercepts responses from /analyze to validate 
    PII and Schema compliance before reaching the client.
    """
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    response = await call_next(request)
    
    # Only intercept successful /analyze responses
    if request.url.path == "/analyze" and response.status_code == 200:
        # Consume the response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
            
        try:
            content = body.decode()
            
            # Guardrail: Check for PII
            if detect_pii(content):
                logger.error("SECURITY VIOLATION: PII detected in response.")
                return JSONResponse(
                    status_code=502,
                    content={"detail": "Safety Violation: PII Detected"}
                )
            
            # Guardrail: Schema Validation
            try:
                parsed = json.loads(content)
                PatientAnalysis(**parsed)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"SCHEMA VIOLATION: {e}")
                return JSONResponse(
                    status_code=502,
                    content={"detail": "Safety Violation: Invalid Schema Output"}
                )
                
            # Re-construct response if safe
            return Response(
                content=body,
                status_code=200,
                media_type="application/json",
                headers={"x-trace-id": trace_id},
            )
            
        except Exception as e:
            logger.error(f"Middleware Error: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal Guardrail Error"})

    return response

# --- 4. The "Orchestration" (Resilience) ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
    reraise=True
)
async def call_llm(prompt: str) -> str:
    global failure_counter
    # Target local Ollama instance
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": f"Summarize this patient data into JSON with keys 'summary', 'risk_level', and 'recommended_action'. Data: {prompt}",
        "stream": False,
        "format": "json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            failure_counter = 0 
            return response.json().get("response", "")
    except httpx.HTTPError:
        failure_counter += 1
        raise

def fallback_response() -> Dict[str, Any]:
    return {
        "summary": "Circuit Breaker Active: Automated summary unavailable.",
        "risk_level": 0,
        "recommended_action": "Consult manual patient records due to system instability."
    }

# --- 1. The "Harness" (Endpoint) ---
@app.post("/analyze")
async def analyze_patient_data(data: AnalysisRequest):
    global failure_counter
    
    patient_info = data.patient_data
    if detect_pii(patient_info) and not data.sensitive_input_approved:
        return JSONResponse(
            status_code=400,
            content={"detail": "Sensitive input requires explicit approval"},
        )
    
    if failure_counter >= CIRCUIT_BREAKER_LIMIT:
        logger.warning("Circuit breaker tripped!")
        return fallback_response()

    try:
        raw_llm_output = await call_llm(patient_info)
        return json.loads(raw_llm_output) # Middleware will catch and validate this
    except httpx.HTTPError:
        return fallback_response()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
