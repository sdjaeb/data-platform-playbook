package manifest.policy

import rego.v1

default allow := false

# Allow if no critical vulnerabilities
allow if not has_critical_vulnerabilities

has_critical_vulnerabilities if input.severity == "CRITICAL"

# Add reason for the verdict
verdict := "Safe" if allow

verdict := "Rejected - Critical Vulnerability Detected" if has_critical_vulnerabilities
