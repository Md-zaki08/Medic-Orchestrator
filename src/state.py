from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class WasteClass(str, Enum):
    INFECTIOUS = "Infectious (Class 6.2)"
    SHARPS = "Sharps (Class 6.2)"
    CHEMICAL = "Chemical Hazardous (Class 9)"
    RADIOACTIVE = "Radioactive (Class 7)"
    GENERAL = "General Municipal (Class 9.1)"
    UNCLASSIFIED = "Unclassified"


class DisposalMethod(str, Enum):
    AUTOCLAVE = "Autoclave Sterilization"
    INCINERATION = "High-Temp Incineration"
    NEUTRALIZATION = "Chemical Neutralization"
    RADIOACTIVE_STORAGE = "Decay in Storage / Deep Geologic Repository"
    LANDFILL = "Municipal Landfill"
    PENDING = "Pending Classification"


class TransportMode(str, Enum):
    ROAD_SECURE = "Secure Road Freight"
    ROAD_STANDARD = "Standard Road Freight"
    AIR_RESTRICTED = "Restricted Cargo Air"


class AuditStatus(str, Enum):
    APPROVED = "APPROVED"
    VETOED = "VETOED"
    PENDING_HITL = "PENDING_HUMAN_APPROVAL"


class InputManifest(BaseModel):
    manifest_id: str = Field(..., description="Unique manifest ID")
    facility_name: str = Field(..., description="Origin facility name")
    declared_contents: str = Field(..., description="Declared text contents")
    estimated_weight_kg: float = Field(..., description="Estimated container weight")
    contact_email: str = Field("anonymous@hospital.org", description="Contact email")
    raw_sensor_data: Dict[str, float] = Field(
        default_factory=dict,
        description="Physical sensor inputs (radiation_uSv_h, temperature_c, ph)"
    )


class ClassificationResult(BaseModel):
    assigned_class: WasteClass = WasteClass.UNCLASSIFIED
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reconciliation_notes: str = Field("", description="Comparison of manifest, sensor, and database")
    requires_special_permit: bool = False


class RoutingPlan(BaseModel):
    selected_facility_id: str = "PENDING"
    selected_facility_name: str = "PENDING"
    estimated_cost_usd: float = 0.0
    route_risk_exposure_index: float = Field(0.0, description="Pedestrian proximity risk")
    recommended_transport_mode: TransportMode = TransportMode.ROAD_STANDARD


class ComplianceAudit(BaseModel):
    is_compliant: bool = False
    violations: List[str] = Field(default_factory=list)
    cited_regulations: List[str] = Field(default_factory=list)
    final_disposal_method: DisposalMethod = DisposalMethod.PENDING


class ExecutionResult(BaseModel):
    action_id: str
    status: AuditStatus = AuditStatus.PENDING_HITL
    approver_badge: Optional[str] = None
    audit_hash: str = ""
    timestamp: Optional[datetime] = Field(default=None)


class MedWasteSessionState(BaseModel):
    session_id: str
    input_manifest: InputManifest
    classification: Optional[ClassificationResult] = None
    routing: Optional[RoutingPlan] = None
    compliance: Optional[ComplianceAudit] = None
    execution: Optional[ExecutionResult] = None
    execution_history: List[str] = Field(
        default_factory=list,
        description="List of state transition stamps"
    )
