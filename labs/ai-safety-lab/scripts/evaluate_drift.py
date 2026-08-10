from difflib import SequenceMatcher
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluator")

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "golden_cases.json"


def load_dataset(path: Path = FIXTURE_PATH):
    return json.loads(path.read_text(encoding="utf-8"))

def calculate_lexical_similarity(a: str, b: str) -> float:
    """Return character-sequence similarity; this is not semantic correctness."""
    return SequenceMatcher(None, a, b).ratio()

def evaluate_model(actual_outputs, split=None):
    """
    Compares actual LLM outputs against the Golden Dataset.
    actual_outputs: List of dicts matching the PatientAnalysis schema.
    """
    dataset = load_dataset()
    cases = [
        case for case in dataset["cases"]
        if "expected" in case and (split is None or case["split"] == split)
    ]
    if len(actual_outputs) != len(cases):
        raise ValueError(f"expected {len(cases)} outputs, received {len(actual_outputs)}")
    results = []
    total_score = 0
    
    for i, item in enumerate(cases):
        actual = actual_outputs[i]
        expected = item["expected"]
        
        # Calculate semantic similarity for summary
        summary_sim = calculate_lexical_similarity(actual["summary"], expected["summary"])
        
        # Exact match for risk level
        risk_match = 1.0 if actual["risk_level"] == expected["risk_level"] else 0.0
        
        # Semantic similarity for action
        action_sim = calculate_lexical_similarity(actual["recommended_action"], expected["recommended_action"])
        
        # Weighted average score
        weighted_score = (summary_sim * 0.5) + (risk_match * 0.3) + (action_sim * 0.2)
        total_score += weighted_score
        
        results.append({
            "id": item["id"],
            "split": item["split"],
            "score": weighted_score,
            "summary_similarity": summary_sim,
            "risk_match": risk_match,
            "action_similarity": action_sim
        })
        
    avg_score = total_score / len(cases)
    return avg_score, results

if __name__ == "__main__":
    # Mocking LLM outputs for demonstration of the script
    # In a real CI/CD, you would call the /analyze endpoint here.
    mock_llm_outputs = [
        case["expected"] for case in load_dataset()["cases"] if "expected" in case
    ]
    
    logger.info("Starting Semantic Drift Evaluation...")
    avg, details = evaluate_model(mock_llm_outputs)
    
    print("\n" + "="*40)
    print("EVALUATION REPORT")
    print("="*40)
    print(f"Average Demonstration Score: {avg:.2%}")
    print("-" * 40)
    
    for res in details:
        print(f"Test Case {res['id']}: Score {res['score']:.2%}")
        print(f"  - Summary Similarity: {res['summary_similarity']:.2%}")
        print(f"  - Risk Level Match:   {res['risk_match']}")
    
    threshold = load_dataset()["threshold"]
    if avg < threshold:
        print("\n[!] FAILURE: Semantic drift detected. Accuracy below threshold.")
        exit(1)
    else:
        print("\n[✓] SUCCESS: Model performance within acceptable limits.")
        exit(0)
