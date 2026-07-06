# Medic Orchestrator Agent Configuration

## Agent: medic-orchestrator

### Description
Multi-agent medical waste disposal orchestrator for the Agents for Good track at Google x Kaggle AI Agents Capstone 2026.

### Architecture
- Framework: Google ADK (google-adk >= 2.0.0)
- Models: Gemini 2.5 Flash (classifier/logistics) + Gemini 2.5 Pro (regulatory auditor)
- Memory: SQLite vector emulation (offline) / PostgreSQL + pgvector (production)
- Tools Protocol: MCP (Model Context Protocol)

### Agents
1. **Medical Orchestrator** (Root) - Sequences workflow, gates decisions
2. **Bio-Classifier** (Flash) - Three-source reconciliation waste classification
3. **Logistics Optimizer** (Flash) - Safe routing and facility assignment
4. **Regulatory Compliance Auditor** (Pro) - Zero-tolerance legal compliance
5. **Secure Action Executor** (Deterministic) - HITL-gated execution

### MCP Tools
- fetch_regulatory_compliance()
- get_facility_capacity()
- get_traffic_data()
- redact_pii()
- query_waste_database()

### Security
- Pre-LLM PII redaction enforced
- Prompt injection detection
- STRIDE threat model implemented
- HITL required for hazardous waste movements
- Per-agent tool allow-lists documented
