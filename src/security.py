import re
import structlog
from typing import Dict, Any, List
from src.state import InputManifest, DisposalMethod

logger = structlog.get_logger()

AGENT_TOOL_ACLS: Dict[str, List[str]] = {
    "Medical Orchestrator": ["delegate_to_agent"],
    "Bio-Classifier": ["query_waste_database", "redact_pii"],
    "Logistics Optimizer": ["get_facility_capacity", "get_traffic_data"],
    "Regulatory Compliance Auditor": ["fetch_regulatory_compliance"],
    "Secure Action Executor": ["log_audit_event"],
}


class SecurityException(Exception):
    pass


class SecurityCheckpoint:
    def __init__(self):
        self.injection_patterns = [
            r"ignore.*instructions",
            r"bypass.*security",
            r"system.*prompt",
            r"you are now a.*",
            r"reveal.*secrets",
        ]

    def validate_tool_access(self, agent_name: str, tool_name: str) -> bool:
        allowed = AGENT_TOOL_ACLS.get(agent_name, [])
        if tool_name not in allowed:
            logger.warn("unauthorized_tool_execution_attempt", agent=agent_name, tool=tool_name)
            raise SecurityException(
                f"Access Denied: Agent {agent_name} is unauthorized to run {tool_name}"
            )
        return True

    def scan_for_prompt_injection(self, text: str) -> bool:
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.error("prompt_injection_detected", matched_pattern=pattern)
                return True
        return False

    def redact_pii_text(self, text: str) -> str:
        patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
            (r"\b\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
            (r"\b(Mr|Mrs|Ms|Dr|Prof)\.\s+[A-Z][a-z]+\b", "[REDACTED_NAME]"),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def sanitize_manifest(self, manifest: InputManifest) -> InputManifest:
        if self.scan_for_prompt_injection(manifest.declared_contents):
            raise SecurityException(
                "Security Fault: Malicious prompt injection payload detected."
            )
        manifest.declared_contents = self.redact_pii_text(manifest.declared_contents)
        return manifest

    def enforce_disposal_veto(self, assigned_class: str, proposed_method: str):
        veto_methods = [
            DisposalMethod.LANDFILL.value,
            DisposalMethod.INCINERATION.value,
            DisposalMethod.AUTOCLAVE.value,
        ]
        if "Radioactive" in assigned_class and proposed_method in veto_methods:
            logger.critical(
                "security_veto_activated",
                class_type=assigned_class,
                method=proposed_method,
            )
            raise SecurityException(
                f"CRITICAL VETO: Cannot process {assigned_class} waste via {proposed_method}. "
                "This action is blocked to prevent public hazardous contamination."
            )
