# Security Architecture

## STRIDE Threat Model

| Category | Threat | Mitigation |
|----------|--------|------------|
| **Spoofing** | Unauthorized manifest submission | API key validation for MCP calls |
| **Tampering** | Manifest modification during handoff | Pydantic signed state models |
| **Repudiation** | Denial of hazardous movement approval | Immutable audit trail in SQLite |
| **Information Disclosure** | PII leakage to LLM traces | Pre-LLM redaction middleware |
| **Denial of Service** | Flooding agent platform | Rate limiting (3 req/s), token budgets |
| **Elevation of Privilege** | Sub-agent executing unauthorized tools | Per-agent tool allow-lists (ACLs) |

## Pre-LLM Security Checkpoint

All inputs pass through a hard-coded, zero-LLM processing pipeline before reaching any model:

1. **PII Redaction**: Regex-based HIPAA compliance (SSN, email, phone, names)
2. **Prompt Injection Detection**: Pattern matching for attack vectors
3. **Rate Limiting**: 3 requests/second default
4. **Tool ACLs**: Each agent restricted to its allow-list

## Guardrail Demo

The guardrail trip scenario (`fixtures/guardrail_trip.json`) demonstrates the system refusing to dispose of radioactive Cobalt-60 in a standard landfill — a critical safety veto.
