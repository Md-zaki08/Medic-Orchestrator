from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json

app = FastAPI(title="Medic Orchestrator Mock Server", version="1.0.0")

REGULATIONS = {
    "Infectious (Class 6.2)": {
        "allowed": ["High-Temp Incineration", "Autoclave Sterilization"],
        "restrictions": ["Maximum transit weight 1000kg"],
    },
    "Sharps (Class 6.2)": {
        "allowed": ["Autoclave Sterilization", "High-Temp Incineration"],
        "restrictions": ["Must use puncture-proof double-walled containers"],
    },
    "Radioactive (Class 7)": {
        "allowed": ["Decay in Storage / Deep Geologic Repository"],
        "restrictions": ["VETO on municipal landfill", "VETO on incineration"],
    },
}

FACILITIES = {
    "FAC_AUTOCLAVE_CENTRAL": {
        "name": "Central Sterilization Autoclave Facility",
        "supported_methods": ["Autoclave Sterilization"],
        "current_capacity_kg": 3000.0,
        "max_capacity_kg": 12000.0,
        "utilization": 0.25,
        "status": "ACTIVE",
    },
    "FAC_RADIO_SAFE": {
        "name": "Deep-Shield Radioactive Containment Site",
        "supported_methods": ["Decay in Storage / Deep Geologic Repository"],
        "current_capacity_kg": 1200.0,
        "max_capacity_kg": 5000.0,
        "utilization": 0.24,
        "status": "ACTIVE",
    },
}


class ManifestSubmission(BaseModel):
    manifest_id: str
    facility_name: str
    declared_contents: str
    estimated_weight_kg: float
    raw_sensor_data: Dict[str, float]


@app.get("/api/regulations/{waste_type}")
async def get_regulations(waste_type: str):
    rules = REGULATIONS.get(waste_type, REGULATIONS.get("default"))
    if not rules:
        raise HTTPException(status_code=404, detail="Waste type not found")
    return {"waste_type": waste_type, **rules}


@app.get("/api/facilities/{facility_id}")
async def get_facility(facility_id: str):
    facility = FACILITIES.get(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility


@app.post("/api/manifests")
async def submit_manifest(manifest: ManifestSubmission):
    return {
        "status": "received",
        "manifest_id": manifest.manifest_id,
        "message": "Manifest logged for processing",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "medic-orchestrator-mock"}
