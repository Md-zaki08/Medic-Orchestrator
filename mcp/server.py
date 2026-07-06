import os
import json
import re
from fastmcp import FastMCP
from typing import Dict, Any

mcp = FastMCP("medic_mcp_server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_REGULATIONS_PATH = os.path.join(BASE_DIR, "mock_db", "regulations.json")
MOCK_FACILITIES_PATH = os.path.join(BASE_DIR, "mock_db", "facilities.json")


def _load_db(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


@mcp.tool()
async def fetch_regulatory_compliance(waste_type: str, jurisdiction: str = "US-Federal") -> str:
    """Queries regulatory databases (EPA/WHO) for safety guidelines and laws."""
    db = _load_db(MOCK_REGULATIONS_PATH)
    rules = db.get(waste_type, db.get("default", {}))
    return json.dumps({
        "jurisdiction": jurisdiction,
        "waste_type": waste_type,
        "allowed_disposal_methods": rules.get("allowed", []),
        "restrictions": rules.get("restrictions", []),
        "licensing_required": rules.get("licensing_required", True),
    })


@mcp.tool()
async def get_facility_capacity(facility_id: str) -> str:
    """Queries live storage levels, maximum capacities, and operating status of a disposal plant."""
    db = _load_db(MOCK_FACILITIES_PATH)
    facility = db.get(facility_id)
    if not facility:
        return json.dumps({"error": f"Facility {facility_id} not found."})
    return json.dumps(facility)


@mcp.tool()
async def get_traffic_data(route_id: str) -> str:
    """Checks the pedestrian density index and transit safety scores of transportation routes."""
    routes = {
        "RT_PRIME": {"risk_index": 0.15, "average_transit_time_min": 45, "congestion": "Low"},
        "RT_DOWNTOWN": {"risk_index": 0.85, "average_transit_time_min": 75, "congestion": "High"},
        "RT_SUBURB": {"risk_index": 0.40, "average_transit_time_min": 60, "congestion": "Medium"},
    }
    return json.dumps(routes.get(route_id, routes["RT_PRIME"]))


@mcp.tool()
async def redact_pii(text: str) -> str:
    """Regex-based high-speed HIPAA PII redaction layer."""
    patterns = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
        (r"\b\+?\d{1,3}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[REDACTED_PHONE]"),
        (r"\b(Mr|Mrs|Ms|Dr|Prof)\.\s+[A-Z][a-z]+\b", "[REDACTED_NAME]"),
    ]
    redacted = text
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


@mcp.tool()
async def query_waste_database(waste_id: str) -> str:
    """Retrieves historical manifests and chemical properties of disposal records."""
    records = {
        "CHEM_902": {"substance": "Formaldehyde solution", "toxicity": "High", "ph": 4.0},
        "BIO_101": {
            "substance": "Cultured medical biologicals",
            "toxicity": "Infectious",
            "ph": 7.2,
        },
        "RAD_701": {
            "substance": "Cobalt-60 source container",
            "toxicity": "Ionizing Radiation",
            "ph": 7.0,
        },
    }
    return json.dumps(
        records.get(waste_id, {
            "substance": "Unknown compound",
            "toxicity": "Unverified",
            "ph": 7.0,
        })
    )
