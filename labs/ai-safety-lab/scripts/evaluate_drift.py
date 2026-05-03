import json
from difflib import SequenceMatcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator")

# --- 3. The "Evaluation Suite" (Golden Dataset) ---
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

def calculate_similarity(a: str, b: str) -> float:
    """Returns a similarity score between 0 and 1."""
    return SequenceMatcher(None, a, b).ratio()

def evaluate_model(actual_outputs):
    """
    Compares actual LLM outputs against the Golden Dataset.
    actual_outputs: List of dicts matching the PatientAnalysis schema.
    """
    results = []
    total_score = 0
    
    for i, item in enumerate(GOLDEN_DATASET):
        actual = actual_outputs[i]
        expected = item["expected"]
        
        # Calculate semantic similarity for summary
        summary_sim = calculate_similarity(actual["summary"], expected["summary"])
        
        # Exact match for risk level
        risk_match = 1.0 if actual["risk_level"] == expected["risk_level"] else 0.0
        
        # Semantic similarity for action
        action_sim = calculate_similarity(actual["recommended_action"], expected["recommended_action"])
        
        # Weighted average score
        weighted_score = (summary_sim * 0.5) + (risk_match * 0.3) + (action_sim * 0.2)
        total_score += weighted_score
        
        results.append({
            "index": i,
            "score": weighted_score,
            "summary_similarity": summary_sim,
            "risk_match": risk_match,
            "action_similarity": action_sim
        })
        
    avg_score = total_score / len(GOLDEN_DATASET)
    return avg_score, results

if __name__ == "__main__":
    # Mocking LLM outputs for demonstration of the script
    # In a real CI/CD, you would call the /analyze endpoint here.
    mock_llm_outputs = [
        {
            "summary": "Patient Sample Patient A has hypertension and is a smoker.",
            "risk_level": 3,
            "recommended_action": "Prescribe medicine and stop smoking."
        },
        {
            "summary": "Healthy Sample Patient B with normal vitals.",
            "risk_level": 1,
            "recommended_action": "Check again next year."
        }
    ]
    
    logger.info("Starting Semantic Drift Evaluation...")
    avg, details = evaluate_model(mock_llm_outputs)
    
    print("\n" + "="*40)
    print(f"EVALUATION REPORT")
    print("="*40)
    print(f"Average Accuracy Score: {avg:.2%}")
    print("-" * 40)
    
    for res in details:
        print(f"Test Case {res['index']}: Score {res['score']:.2%}")
        print(f"  - Summary Similarity: {res['summary_similarity']:.2%}")
        print(f"  - Risk Level Match:   {res['risk_match']}")
    
    threshold = 0.80
    if avg < threshold:
        print("\n[!] FAILURE: Semantic drift detected. Accuracy below threshold.")
        exit(1)
    else:
        print("\n[✓] SUCCESS: Model performance within acceptable limits.")
        exit(0)
