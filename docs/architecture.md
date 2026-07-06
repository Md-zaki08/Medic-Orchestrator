# Medic Orchestrator Architecture

## Multi-Agent ADK Graph

```
                    ┌─────────────────────────────────────────┐
                    │       MEDIC ORCHESTRATOR (Root)         │
                    │      Model: Gemini 2.5 Pro              │
                    │  Coordinates state handoffs, gates on   │
                    │  results, conditional loop branching    │
                    └────────────────────┬────────────────────┘
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
 ┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
 │    BIO-CLASSIFIER    │   │  LOGISTICS OPTIMIZER │   │  REGULATORY AUDITOR  │
 │ Model: Gemini Flash  │   │ Model: Gemini Flash  │   │ Model: Gemini Pro    │
 │ Reconciles Manifest  │   │ Calculates safest    │   │ Strict zero-tolerance│
 │ vs Sensor vs WHO DB  │   │ routes, capacity     │   │ compliance check     │
 └──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                   ┌─────────────────────────────────────────┐
                   │        SECURE ACTION EXECUTOR           │
                   │          Model: Deterministic           │
                   │ Enforces HITL check on hazardous waste, │
                   │ writes to immutable SQLite Audit Log    │
                   └─────────────────────────────────────────┘
```

## Data Flow

1. Clinic submits manifest with sensor telemetry
2. Security middleware sanitizes PII and checks for prompt injection
3. Bio-Classifier runs three-source reconciliation
4. Logistics Optimizer matches waste to facility
5. Regulatory Auditor checks compliance
6. Security veto checks for radioactive/landfill violations
7. Secure Action Executor requires HITL for hazardous waste

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Google ADK |
| Models | Gemini 2.5 Flash / Pro |
| Tools | FastMCP Server |
| Memory | SQLite + pgvector (PostgreSQL) |
| Security | Pre-LLM middleware + STRIDE |
| Frontend | Streamlit |
| API | FastAPI mock server |
| Testing | pytest-asyncio |
