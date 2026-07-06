import structlog
from src.state import InputManifest, ClassificationResult, WasteClass
from src.agents.base import BaseMedicAgent

logger = structlog.get_logger()


class BioClassifierAgent(BaseMedicAgent):
    agent_name = "Bio-Classifier"

    async def classify(self, manifest: InputManifest) -> ClassificationResult:
        logger.info("classifying_waste", manifest_id=manifest.manifest_id)
        sensor = manifest.raw_sensor_data
        declared = manifest.declared_contents.lower()
        notes = []

        radiation = sensor.get("radiation_uSv_h", 0.0)
        temperature = sensor.get("temperature_c", 25.0)
        ph = sensor.get("ph", 7.0)

        if radiation > 1.0:
            notes.append(f"Radiation {radiation}uSv/h exceeds threshold -> RADIOACTIVE")
            return ClassificationResult(
                assigned_class=WasteClass.RADIOACTIVE,
                confidence=0.95,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=True,
            )

        if temperature > 40.0:
            notes.append(f"Temperature {temperature}C suggests biological activity")
            return ClassificationResult(
                assigned_class=WasteClass.INFECTIOUS,
                confidence=0.85,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=True,
            )

        if ph < 4.0 or ph > 10.0:
            notes.append(f"pH {ph} outside safe range -> CHEMICAL")
            return ClassificationResult(
                assigned_class=WasteClass.CHEMICAL,
                confidence=0.90,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=True,
            )

        chem_keywords = ["solvent", "chemical", "reagent", "hazmat", "toxic", "corrosive"]
        if any(kw in declared for kw in chem_keywords):
            notes.append(f"Manifest indicates chemical waste -> CHEMICAL")
            return ClassificationResult(
                assigned_class=WasteClass.CHEMICAL,
                confidence=0.85,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=True,
            )

        if "needle" in declared or "sharp" in declared or "syringe" in declared:
            notes.append("Manifest contains sharp objects -> SHARPS")
            return ClassificationResult(
                assigned_class=WasteClass.SHARPS,
                confidence=0.90,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=False,
            )

        if "bio" in declared or "infectious" in declared or "culture" in declared:
            notes.append("Manifest indicates biological material -> INFECTIOUS")
            return ClassificationResult(
                assigned_class=WasteClass.INFECTIOUS,
                confidence=0.80,
                reconciliation_notes=" | ".join(notes),
                requires_special_permit=True,
            )

        notes.append("No anomalies detected -> GENERAL MUNICIPAL")
        return ClassificationResult(
            assigned_class=WasteClass.GENERAL,
            confidence=0.95,
            reconciliation_notes=" | ".join(notes),
            requires_special_permit=False,
        )

    async def execute(self, state):
        return await self.classify(state.input_manifest)
