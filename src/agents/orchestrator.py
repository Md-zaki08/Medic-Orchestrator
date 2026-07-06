import structlog
from src.state import MedWasteSessionState, AuditStatus
from src.security import SecurityCheckpoint, SecurityException
from src.agents.classifier import BioClassifierAgent
from src.agents.logistics import LogisticsOptimizerAgent
from src.agents.auditor import RegulatoryAuditorAgent
from src.agents.executor import SecureExecutorAgent

logger = structlog.get_logger()


class MedWasteGraphOrchestrator:
    def __init__(self):
        self.security = SecurityCheckpoint()
        self.classifier = BioClassifierAgent()
        self.logistics = LogisticsOptimizerAgent()
        self.auditor = RegulatoryAuditorAgent()
        self.executor = SecureExecutorAgent()

    async def execute_run(self, session: MedWasteSessionState) -> MedWasteSessionState:
        session.execution_history.append(f"Run started: {session.session_id}")
        logger.info("orchestration_run_initiated", session_id=session.session_id)

        try:
            session.input_manifest = self.security.sanitize_manifest(session.input_manifest)
            session.execution_history.append("Input sanitized (PII/injection check passed)")

            session.classification = await self.classifier.classify(session.input_manifest)
            session.execution_history.append(
                f"Classification: {session.classification.assigned_class.value} "
                f"(confidence={session.classification.confidence:.2f})"
            )

            if session.classification.confidence < 0.8:
                logger.warn("low_classification_confidence", confidence=session.classification.confidence)
                session.execution_history.append("WARNING: Low classification confidence flagged")

            session.routing = await self.logistics.calculate_routing(session.classification)
            session.execution_history.append(
                f"Routing: {session.routing.selected_facility_name} "
                f"(risk={session.routing.route_risk_exposure_index:.2f})"
            )

            session.compliance = await self.auditor.audit_compliance(
                session.classification, session.routing
            )
            session.execution_history.append(
                f"Compliance: {'COMPLIANT' if session.compliance.is_compliant else 'NON-COMPLIANT'}"
            )

            self.security.enforce_disposal_veto(
                session.classification.assigned_class.value,
                session.compliance.final_disposal_method.value,
            )

            session.execution = await self.executor.commit_disposal(session)
            session.execution_history.append(f"Execution: {session.execution.status.value}")

        except SecurityException as se:
            logger.error("security_blockade_active", error=str(se))
            session.execution_history.append(f"SECURITY FAULT: {str(se)}")
            if session.compliance is None:
                from src.state import ComplianceAudit
                session.compliance = ComplianceAudit()
            session.compliance.is_compliant = False
            session.compliance.violations.append(str(se))
            from src.state import ExecutionResult, AuditStatus
            import uuid
            session.execution = ExecutionResult(
                action_id=str(uuid.uuid4()),
                status=AuditStatus.VETOED,
            )

        except Exception as e:
            logger.critical("orchestration_unhandled_failure", error=str(e))
            session.execution_history.append(f"SYSTEM ERROR: {str(e)}")

        return session
