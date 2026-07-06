import asyncio
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st

st.set_page_config(
    page_title="Medic Orchestrator",
    page_icon="🏥",
    layout="wide",
)

from src.state import InputManifest, MedWasteSessionState, WasteClass, AuditStatus
from src.graph import MedWasteGraphOrchestrator


async def run_orchestrator(manifest: InputManifest) -> MedWasteSessionState:
    session = MedWasteSessionState(
        session_id=f"web-{uuid.uuid4().hex[:8]}",
        input_manifest=manifest,
    )
    orchestrator = MedWasteGraphOrchestrator()
    return await orchestrator.execute_run(session)


def main():
    st.title("🏥 Medic Orchestrator")
    st.markdown("### Medical Waste Disposal Multi-Agent System")
    st.markdown("*Google × Kaggle AI Agents Capstone 2026 — Agents for Good Track*")

    with st.sidebar:
        st.header("Clinic Input Panel")
        manifest_id = st.text_input("Manifest ID", value=f"M-{uuid.uuid4().hex[:6].upper()}")
        facility_name = st.text_input("Facility Name", value="City General Hospital")
        declared_contents = st.text_area(
            "Declared Contents",
            value="Soiled dressings and used needles from oncology department",
            height=100,
        )
        weight = st.number_input("Estimated Weight (kg)", min_value=0.1, value=24.5, step=0.5)

        st.subheader("IoT Sensor Telemetry")
        col1, col2, col3 = st.columns(3)
        with col1:
            radiation = st.number_input("Radiation (uSv/h)", value=0.12, format="%.2f")
        with col2:
            temperature = st.number_input("Temperature (°C)", value=22.0, format="%.1f")
        with col3:
            ph = st.number_input("pH Level", value=7.1, format="%.1f")

        submitted = st.button("Submit for Processing", type="primary")

    col_main, col_side = st.columns([3, 1])

    with col_side:
        st.subheader("System Status")
        st.markdown("🟢 **MCP Server**: Ready")
        st.markdown("🟢 **Gemini API**: Connected")
        st.markdown("🟢 **Memory Store**: Active")

    with col_main:
        if submitted:
            manifest = InputManifest(
                manifest_id=manifest_id,
                facility_name=facility_name,
                declared_contents=declared_contents,
                estimated_weight_kg=weight,
                raw_sensor_data={
                    "radiation_uSv_h": radiation,
                    "temperature_c": temperature,
                    "ph": ph,
                },
            )

            with st.spinner("Running multi-agent pipeline..."):
                result = asyncio.run(run_orchestrator(manifest))

            st.subheader("Pipeline Flow")

            steps = result.execution_history
            for i, step in enumerate(steps):
                if "SECURITY FAULT" in step or "ERROR" in step or "VETO" in step:
                    st.error(f"**Step {i+1}**: {step}")
                elif "APPROVED" in step:
                    st.success(f"**Step {i+1}**: {step}")
                elif "WARNING" in step:
                    st.warning(f"**Step {i+1}**: {step}")
                else:
                    st.info(f"**Step {i+1}**: {step}")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Classification Result")
                if result.classification:
                    c = result.classification
                    class_color = {
                        WasteClass.RADIOACTIVE: "red",
                        WasteClass.INFECTIOUS: "orange",
                        WasteClass.CHEMICAL: "yellow",
                        WasteClass.SHARPS: "blue",
                        WasteClass.GENERAL: "green",
                    }.get(c.assigned_class, "gray")

                    st.markdown(f"**Waste Class**: :{class_color}[{c.assigned_class.value}]")
                    st.markdown(f"**Confidence**: {c.confidence:.0%}")
                    st.markdown(f"**Reconciliation**: {c.reconciliation_notes}")

                st.subheader("Routing Plan")
                if result.routing:
                    r = result.routing
                    st.markdown(f"**Facility**: {r.selected_facility_name}")
                    st.markdown(f"**Cost**: ${r.estimated_cost_usd:,.0f}")
                    st.markdown(f"**Risk Index**: {r.route_risk_exposure_index:.2f}")

            with col2:
                st.subheader("Compliance Audit")
                if result.compliance:
                    comp = result.compliance
                    if comp.is_compliant:
                        st.success("COMPLIANT")
                    else:
                        st.error("NON-COMPLIANT")
                    if comp.violations:
                        for v in comp.violations:
                            st.warning(f"⚠ {v}")
                    st.markdown(f"**Disposal Method**: {comp.final_disposal_method.value}")
                    if comp.cited_regulations:
                        st.markdown("**Regulations Cited**:")
                        for reg in comp.cited_regulations:
                            st.markdown(f"- {reg}")

                st.subheader("Execution Status")
                if result.execution:
                    e = result.execution
                    status_icon = {
                        AuditStatus.APPROVED: ("✅", "green"),
                        AuditStatus.VETOED: ("❌", "red"),
                        AuditStatus.PENDING_HITL: ("⏳", "yellow"),
                    }.get(e.status, ("❓", "gray"))
                    st.markdown(f"{status_icon[0]} **Status**: :{status_icon[1]}[{e.status.value}]")
                    st.code(f"Audit: {e.audit_hash[:24]}...")

            if result.execution and result.execution.status == AuditStatus.PENDING_HITL:
                st.subheader("Human-in-the-Loop Approval Required")
                st.warning("This disposal requires manual override validation.")
                badge = st.text_input("Enter Supervisor Badge ID", placeholder="e.g., HD-701")
                if st.button("Approve Disposal"):
                    result.execution.status = AuditStatus.APPROVED
                    result.execution.approver_badge = badge
                    st.success(f"Approved by {badge}. Disposal logged to audit trail.")
                if st.button("Veto Action"):
                    result.execution.status = AuditStatus.VETOED
                    st.error("Action vetoed by supervisor.")

            st.download_button(
                "Download Session Report",
                data=result.model_dump_json(indent=2),
                file_name=f"session_{result.session_id}.json",
                mime="application/json",
            )
        else:
            st.info("Enter clinic details in the sidebar and click 'Submit for Processing' to run the multi-agent pipeline.")
            st.markdown("---")
            st.markdown("### Quick Demo Scenarios")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Biohazard Spill**")
                st.markdown("Infectious waste → Autoclave route")
            with col2:
                st.markdown("**Radioactive Mismatch**")
                st.markdown("Mislabeled → Security Veto")
            with col3:
                st.markdown("**General Waste**")
                st.markdown("Standard → Auto-approved")


if __name__ == "__main__":
    main()
