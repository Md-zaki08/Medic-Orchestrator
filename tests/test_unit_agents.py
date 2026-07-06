import pytest
from src.state import (
    InputManifest,
    ClassificationResult,
    WasteClass,
    RoutingPlan,
    ComplianceAudit,
    DisposalMethod,
    AuditStatus,
    MedWasteSessionState,
)


class TestInputManifestValidation:
    def test_valid_manifest(self, sample_manifest_sharps):
        assert sample_manifest_sharps.manifest_id == "TEST-001"
        assert sample_manifest_sharps.estimated_weight_kg == 10.0

    def test_empty_sensor_data_defaults(self):
        m = InputManifest(
            manifest_id="M1",
            facility_name="F",
            declared_contents="test",
            estimated_weight_kg=1.0,
        )
        assert m.raw_sensor_data == {}

    def test_contact_email_default(self):
        m = InputManifest(
            manifest_id="M1",
            facility_name="F",
            declared_contents="test",
            estimated_weight_kg=1.0,
        )
        assert m.contact_email == "anonymous@hospital.org"


class TestClassificationResult:
    def test_default_unclassified(self):
        c = ClassificationResult()
        assert c.assigned_class == WasteClass.UNCLASSIFIED
        assert c.confidence == 0.0
        assert c.requires_special_permit is False

    def test_high_confidence(self):
        c = ClassificationResult(
            assigned_class=WasteClass.INFECTIOUS,
            confidence=0.95,
            requires_special_permit=True,
        )
        assert c.confidence == 0.95
        assert c.requires_special_permit is True

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            ClassificationResult(confidence=1.5)


class TestRoutingPlan:
    def test_default_pending(self):
        r = RoutingPlan()
        assert r.selected_facility_id == "PENDING"
        assert r.estimated_cost_usd == 0.0

    def test_secure_transport(self):
        r = RoutingPlan(
            selected_facility_id="FAC_001",
            selected_facility_name="Test Facility",
            estimated_cost_usd=5000.0,
            route_risk_exposure_index=0.15,
        )
        assert r.estimated_cost_usd == 5000.0


class TestComplianceAudit:
    def test_default_non_compliant(self):
        c = ComplianceAudit()
        assert c.is_compliant is False
        assert c.violations == []

    def test_with_violations(self):
        c = ComplianceAudit(
            is_compliant=False,
            violations=["Radioactive waste to landfill"],
            cited_regulations=["EPA Title 40 CFR"],
            final_disposal_method=DisposalMethod.LANDFILL,
        )
        assert len(c.violations) == 1
        assert c.final_disposal_method == DisposalMethod.LANDFILL


class TestExecutionResult:
    def test_default_pending_hitl(self):
        e = create_execution_result("ACT-001")
        assert e.status == AuditStatus.PENDING_HITL

    def test_approved_with_badge(self):
        e = create_execution_result("ACT-002")
        e.status = AuditStatus.APPROVED
        e.approver_badge = "HD-701"
        assert e.status == AuditStatus.APPROVED
        assert e.approver_badge == "HD-701"


def create_execution_result(action_id: str):
    from datetime import datetime
    from src.state import ExecutionResult
    return ExecutionResult(
        action_id=action_id,
        audit_hash="abc123",
    )


class TestSessionState:
    def test_full_session(self, sample_manifest_sharps):
        session = MedWasteSessionState(
            session_id="full-test",
            input_manifest=sample_manifest_sharps,
        )
        assert session.session_id == "full-test"
        assert session.classification is None
        assert len(session.execution_history) == 0

    def test_execution_history_append(self, sample_session):
        sample_session.execution_history.append("Step 1: Sanitize")
        sample_session.execution_history.append("Step 2: Classify")
        assert len(sample_session.execution_history) == 2
