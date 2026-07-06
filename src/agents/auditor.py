import structlog
from src.state import (
    ClassificationResult,
    RoutingPlan,
    ComplianceAudit,
    DisposalMethod,
    WasteClass,
)
from src.agents.base import BaseMedicAgent

logger = structlog.get_logger()

REGULATION_MAP = {
    WasteClass.RADIOACTIVE: {
        "allowed": [DisposalMethod.RADIOACTIVE_STORAGE],
        "citations": [
            "EPA Title 40 CFR Part 190 – Environmental Radiation Protection Standards",
            "WHO Ionizing Radiation Waste Management Guidelines (2023)",
        ],
    },
    WasteClass.INFECTIOUS: {
        "allowed": [DisposalMethod.INCINERATION, DisposalMethod.AUTOCLAVE],
        "citations": [
            "EPA Title 40 CFR Part 60 – Standards of Performance for Incineration",
            "WHO Biohazard Waste Management Guidelines (2023)",
        ],
    },
    WasteClass.SHARPS: {
        "allowed": [DisposalMethod.AUTOCLAVE, DisposalMethod.INCINERATION],
        "citations": [
            "OSHA Bloodborne Pathogens Standard 29 CFR 1910.1030",
        ],
    },
    WasteClass.CHEMICAL: {
        "allowed": [DisposalMethod.NEUTRALIZATION, DisposalMethod.INCINERATION],
        "citations": [
            "EPA Title 40 CFR Part 261 – Identification of Hazardous Waste",
        ],
    },
    WasteClass.GENERAL: {
        "allowed": [DisposalMethod.LANDFILL, DisposalMethod.AUTOCLAVE],
        "citations": [
            "EPA Title 40 CFR Part 258 – Landfill Standards",
        ],
    },
    WasteClass.UNCLASSIFIED: {
        "allowed": [DisposalMethod.PENDING],
        "citations": [],
    },
}

FACILITY_METHOD_MAP = {
    "FAC_METRO_INCINERATE": DisposalMethod.INCINERATION,
    "FAC_AUTOCLAVE_CENTRAL": DisposalMethod.AUTOCLAVE,
    "FAC_CHEMICAL_NEUTRAL": DisposalMethod.NEUTRALIZATION,
    "FAC_RADIO_SAFE": DisposalMethod.RADIOACTIVE_STORAGE,
}


class RegulatoryAuditorAgent(BaseMedicAgent):
    agent_name = "Regulatory Compliance Auditor"

    async def audit_compliance(
        self, classification: ClassificationResult, routing: RoutingPlan
    ) -> ComplianceAudit:
        logger.info("auditing_compliance", waste_class=classification.assigned_class.value)

        regulations = REGULATION_MAP.get(
            classification.assigned_class, REGULATION_MAP[WasteClass.UNCLASSIFIED]
        )

        method = FACILITY_METHOD_MAP.get(routing.selected_facility_id, DisposalMethod.PENDING)

        violations = []

        if method not in regulations["allowed"]:
            violation = (
                f"Facility {routing.selected_facility_id} uses {method.value} "
                f"but regulations require {[m.value for m in regulations['allowed']]} "
                f"for {classification.assigned_class.value}"
            )
            violations.append(violation)

        if classification.assigned_class == WasteClass.RADIOACTIVE and method in [
            DisposalMethod.LANDFILL,
            DisposalMethod.INCINERATION,
            DisposalMethod.AUTOCLAVE,
        ]:
            violations.append(
                "STRICT VETO: Radioactive waste cannot be processed via standard disposal methods"
            )

        is_compliant = len(violations) == 0

        if is_compliant:
            logger.info("compliance_passed", waste_class=classification.assigned_class.value)
        else:
            logger.warn("compliance_violations_found", violations=violations)

        return ComplianceAudit(
            is_compliant=is_compliant,
            violations=violations,
            cited_regulations=regulations["citations"],
            final_disposal_method=method,
        )

    async def execute(self, state):
        return await self.audit_compliance(state.classification, state.routing)
