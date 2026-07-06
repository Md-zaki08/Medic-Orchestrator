import uuid
import hashlib
import json
import structlog
from datetime import datetime
from datetime import timezone as tz
from src.state import (
    MedWasteSessionState,
    ExecutionResult,
    AuditStatus,
    WasteClass,
    DisposalMethod,
)
from src.agents.base import BaseMedicAgent

logger = structlog.get_logger()


class SecureExecutorAgent(BaseMedicAgent):
    agent_name = "Secure Action Executor"

    async def commit_disposal(self, session: MedWasteSessionState) -> ExecutionResult:
        logger.info("executing_disposal", session_id=session.session_id)
        action_id = str(uuid.uuid4())

        audit_data = {
            "session_id": session.session_id,
            "manifest_id": session.input_manifest.manifest_id,
            "classification": session.classification.model_dump() if session.classification else None,
            "routing": session.routing.model_dump() if session.routing else None,
            "compliance": session.compliance.model_dump() if session.compliance else None,
            "timestamp": datetime.now(tz.utc).isoformat(),
        }
        audit_hash = hashlib.sha256(json.dumps(audit_data, sort_keys=True).encode()).hexdigest()

        if not session.compliance or not session.compliance.is_compliant:
            return ExecutionResult(
                action_id=action_id,
                status=AuditStatus.VETOED,
                audit_hash=audit_hash,
            )

        if session.classification and session.classification.assigned_class in [
            WasteClass.GENERAL,
        ]:
            return ExecutionResult(
                action_id=action_id,
                status=AuditStatus.APPROVED,
                audit_hash=audit_hash,
            )

        return ExecutionResult(
            action_id=action_id,
            status=AuditStatus.PENDING_HITL,
            audit_hash=audit_hash,
        )

    async def execute(self, state):
        return await self.commit_disposal(state)
