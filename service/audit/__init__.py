"""Audit logging — SHA-256 of every input + timestamped JSON Lines per call.

Per the strategic proposal: every inference produces a locally-recorded audit
entry for CDSCO-compliance reproducibility. No network traffic. Path is
configurable via `SKYBRAIN_QVAC_AUDIT_DIR`.
"""
