# Evaluation Lineage

This lab is an illustrative DPP implementation, not a production evaluator.
Its portable evaluation concepts align with Agentic Resource Kit v0.6.0 without
making ARK a runtime dependency.

Track source fixture version, development or held-out split, transformation and
de-identification, candidate configuration, metric version, policy decision,
trace ID, and final human-owned decision. Preserve raw restricted evidence in
an approved private store and publish only sanitized derivatives and digests.

The evaluator uses lexical sequence similarity. It does not measure semantic or
clinical correctness. Its threshold is a documented lab default, not a
production release threshold. Promotion requires domain-owner labels, negative
examples, calibrated evaluators, disagreement analysis, and end-to-end tests.
