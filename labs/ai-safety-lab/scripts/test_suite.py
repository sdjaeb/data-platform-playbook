try:
    from .evaluate_drift import evaluate_model, load_dataset
except ImportError:  # Direct script execution.
    from evaluate_drift import evaluate_model, load_dataset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-suite")

def run_suite(actual_outputs):
    logger.info("Running Official Evaluation Suite...")
    avg, details = evaluate_model(actual_outputs)
    
    print("\n" + "="*40)
    print("OFFICIAL TEST RESULTS")
    print("="*40)
    print(f"Overall Accuracy: {avg:.2%}")
    
    threshold = load_dataset()["threshold"]
    if avg < threshold:
        print(f"\n[!] STATUS: FAIL (Below {threshold:.0%} Demonstration Threshold)")
        return False
    else:
        print("\n[✓] STATUS: PASS")
        return True

if __name__ == "__main__":
    # Example usage with mock data
    mock_data = [
        case["expected"] for case in load_dataset()["cases"] if "expected" in case
    ]
    success = run_suite(mock_data)
    exit(0 if success else 1)
