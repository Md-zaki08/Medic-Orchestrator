import pytest
from src.graph import MedWasteGraphOrchestrator
from src.state import WasteClass, AuditStatus


@pytest.mark.asyncio
async def test_sharps_classification_pipeline(sample_session):
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(sample_session)

    assert result.classification is not None
    assert result.classification.assigned_class == WasteClass.SHARPS
    assert result.classification.confidence >= 0.8
    assert result.routing is not None
    assert result.routing.selected_facility_id != "PENDING"


@pytest.mark.asyncio
async def test_radioactive_detection(sample_manifest_radioactive):
    from src.state import MedWasteSessionState
    session = MedWasteSessionState(
        session_id="test-radio",
        input_manifest=sample_manifest_radioactive,
    )
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(session)

    assert result.classification.assigned_class == WasteClass.RADIOACTIVE
    assert result.classification.requires_special_permit is True
    assert result.routing.selected_facility_id == "FAC_RADIO_SAFE"


@pytest.mark.asyncio
async def test_chemical_classification(sample_manifest_chemical):
    from src.state import MedWasteSessionState
    session = MedWasteSessionState(
        session_id="test-chem",
        input_manifest=sample_manifest_chemical,
    )
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(session)

    assert result.classification.assigned_class == WasteClass.CHEMICAL
    assert result.classification.requires_special_permit is True


@pytest.mark.asyncio
async def test_compliance_veto_on_radioactive(sample_manifest_radioactive):
    from src.state import MedWasteSessionState
    session = MedWasteSessionState(
        session_id="test-veto",
        input_manifest=sample_manifest_radioactive,
    )
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(session)

    assert result.compliance is not None
    assert result.execution is not None


@pytest.mark.asyncio
async def test_pipeline_history_populated(sample_session):
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(sample_session)

    assert len(result.execution_history) >= 5
    assert any("sanitized" in s.lower() for s in result.execution_history)
    assert any("Classification" in s for s in result.execution_history)


@pytest.mark.asyncio
async def test_routing_cost_calculation(sample_session):
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(sample_session)

    assert result.routing.estimated_cost_usd > 0
    assert result.routing.route_risk_exposure_index >= 0


@pytest.mark.asyncio
async def test_executor_requires_hitl_for_hazardous(sample_session):
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(sample_session)

    assert result.execution.status == AuditStatus.PENDING_HITL


@pytest.mark.asyncio
async def test_orchestrator_handles_missing_manifest():
    from src.state import InputManifest, MedWasteSessionState
    manifest = InputManifest(
        manifest_id="EMPTY",
        facility_name="Test",
        declared_contents="",
        estimated_weight_kg=0.0,
    )
    session = MedWasteSessionState(
        session_id="test-empty",
        input_manifest=manifest,
    )
    orchestrator = MedWasteGraphOrchestrator()
    result = await orchestrator.execute_run(session)

    assert result.classification is not None
    assert result.routing is not None
