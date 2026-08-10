from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_evaluator():
    path = ROOT / "scripts" / "evaluate_drift.py"
    spec = importlib.util.spec_from_file_location("evaluate_drift", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load evaluator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvaluationContractTests(unittest.TestCase):
    def test_dataset_has_development_held_out_and_negative_strata(self):
        dataset = load_evaluator().load_dataset()
        splits = {case["split"] for case in dataset["cases"]}
        strata = {value for case in dataset["cases"] for value in case["strata"]}
        self.assertEqual({"development", "held_out"}, splits)
        self.assertIn("negative", strata)
        self.assertIn("privacy", strata)

    def test_metric_is_explicitly_lexical(self):
        evaluator = load_evaluator()
        self.assertEqual(1.0, evaluator.calculate_lexical_similarity("same", "same"))
        self.assertIn("lexical", evaluator.load_dataset()["metric"])


if __name__ == "__main__":
    unittest.main()
