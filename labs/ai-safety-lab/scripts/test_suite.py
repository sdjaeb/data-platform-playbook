import json
from scripts.evaluate_drift import evaluate_model
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-suite")

# --- 3. The "Evaluation Suite" (Golden Dataset) ---
# This matches the logic in evaluate_drift but acts as the official test entry point
GOLDEN_DATASET = [
    {
        "input": "Patient Sample Patient A, 45, has chronic hypertension. BP is 150/95. History of smoking.",
        "expected": {
            "summary": "Patient exhibits hypertension with elevated blood pressure and smoking history.",
            "risk_level": 3,
            "recommended_action": "Prescribe ACE inhibitors and recommend smoking cessation."
        }
    },
    {
        "input": "Patient Sample Patient B, 30, shows no symptoms. Routine checkup. All vitals normal.",
        "expected": {
            "summary": "Healthy patient with normal vitals during routine checkup.",
            "risk_level": 1,
            "recommended_action": "Annual follow-up."
        }
    }
]

def run_suite(actual_outputs):
    logger.info("Running Official Evaluation Suite...")
    avg, details = evaluate_model(actual_outputs)
    
    print("\n" + "="*40)
    print(f"OFFICIAL TEST RESULTS")
    print("="*40)
    print(f"Overall Accuracy: {avg:.2%}")
    
    if avg < 0.80:
        print("\n[!] STATUS: FAIL (Below 80% Threshold)")
        return False
    else:
        print("\n[✓] STATUS: PASS")
        return True

if __name__ == "__main__":
    # Example usage with mock data
    mock_data = [
        {
            "summary": "Patient has high blood pressure and smokes.",
            "risk_level": 3,
            "recommended_action": "Prescribe ACE inhibitors and stop smoking."
        },
        {
            "summary": "Patient is healthy.",
            "risk_level": 1,
            "recommended_action": "Follow up in one year."
        }
    ]
    success = run_suite(mock_data)
    exit(0 if success else 1)
