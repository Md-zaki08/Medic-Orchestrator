import structlog
from src.state import ClassificationResult, RoutingPlan, WasteClass, TransportMode
from src.agents.base import BaseMedicAgent

logger = structlog.get_logger()

FACILITY_MAP = {
    WasteClass.INFECTIOUS: {
        "id": "FAC_METRO_INCINERATE",
        "name": "Metro High-Temp Thermal Incinerator",
        "cost": 4500.0,
    },
    WasteClass.SHARPS: {
        "id": "FAC_AUTOCLAVE_CENTRAL",
        "name": "Central Sterilization Autoclave Facility",
        "cost": 1200.0,
    },
    WasteClass.CHEMICAL: {
        "id": "FAC_CHEMICAL_NEUTRAL",
        "name": "Sovereign Chemical Neutralization Corp",
        "cost": 3800.0,
    },
    WasteClass.RADIOACTIVE: {
        "id": "FAC_RADIO_SAFE",
        "name": "Deep-Shield Radioactive Containment Site",
        "cost": 8500.0,
    },
    WasteClass.GENERAL: {
        "id": "FAC_AUTOCLAVE_CENTRAL",
        "name": "Central Sterilization Autoclave Facility",
        "cost": 500.0,
    },
    WasteClass.UNCLASSIFIED: {
        "id": "PENDING",
        "name": "Pending Classification",
        "cost": 0.0,
    },
}


class LogisticsOptimizerAgent(BaseMedicAgent):
    agent_name = "Logistics Optimizer"

    async def calculate_routing(self, classification: ClassificationResult) -> RoutingPlan:
        logger.info("calculating_routing", waste_class=classification.assigned_class.value)
        facility = FACILITY_MAP.get(
            classification.assigned_class, FACILITY_MAP[WasteClass.UNCLASSIFIED]
        )

        transport = TransportMode.ROAD_SECURE if classification.requires_special_permit else TransportMode.ROAD_STANDARD
        risk = 0.15 if transport == TransportMode.ROAD_SECURE else 0.40

        return RoutingPlan(
            selected_facility_id=facility["id"],
            selected_facility_name=facility["name"],
            estimated_cost_usd=facility["cost"],
            route_risk_exposure_index=risk,
            recommended_transport_mode=transport,
        )

    async def execute(self, state):
        return await self.calculate_routing(state.classification)
