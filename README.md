# banxe-business-processes

ArchiMate 3.2 business process repository for AI agents.

## Structure

```
banxe-business-processes/
├── processes/              ← Business process definitions (ArchiMate / BPMN)
│   ├── strategy/           ← Strategic intent, OKRs
│   ├── onboarding/         ← Customer onboarding, KYC, KYB
│   ├── payments/           ← FPS, SEPA, SEPA Instant rail processes
│   ├── card-lifecycle/     ← Card issuance, activation, blocking
│   ├── compliance/         ← CASS, AML, Consumer Duty, SM&CR
│   ├── treasury/           ← Safeguarding, reconciliation, liquidity
│   ├── risk/               ← Risk assessment, monitoring
│   └── baas/               ← Banking-as-a-Service tenant processes
├── actors/                 ← Actor definitions (roles, responsibilities)
├── services/               ← Application/technology service catalogue
├── models/                 ← Data models, domain objects
├── invariants/             ← Business invariants (I-01..I-29)
├── exchange/               ← Open Exchange XML exports from Archi Tool
├── diagrams/
│   ├── svg/                ← SVG diagram exports
│   └── png/                ← PNG diagram exports
├── ai-agent-context/       ← Context files for AI agents
│   ├── processes-registry.json    ← Generated registry: every process as a process_ref
│   ├── intent-process-map.yaml    ← L1 intent → process_ref resolution table
│   └── process_ref.schema.json    ← process_ref = {process_id, version} contract
└── .claude/                ← Claude Code configuration
```

## Resolvability (ADR-048 / ADR-049)

This repository is the **canonical S13-00 Business Process Repository** — the versioned
source of truth that client intents resolve against before any L2 agent action
(ADR-048 D1/D3). Each process carries a stable **`process_ref = {process_id, version}`**
(ADR-048 D3, ADR-049 D2), alongside its preserved ArchiMate fields.

| Artefact | Role |
|----------|------|
| `processes/**/*.yaml` | Process definitions: ArchiMate fields **+** `process_id`, `version`, `triggers`, `steps`, `actors`, `compliance_refs` |
| `ai-agent-context/processes-registry.json` | Generated registry — the L1 lookup target (one `process_ref` per process) |
| `ai-agent-context/intent-process-map.yaml` | L1 intent → `process_id(s)` resolution table; the 9 client-facing capabilities each resolve |
| `ai-agent-context/process_ref.schema.json` | `{process_id, version}` schema (local mirror of the ADR-048 contract) |

```
make registry   # rebuild processes-registry.json (non-destructive — never clobbers enrichment)
make validate   # assert every process_ref + intent + actor resolves
```

An intent that resolves to **no** process is a governance event (HITL / process-gap),
never improvised (ADR-048 D3.3).

## Workflow

1. Model business processes in **Archi Tool** (free, ArchiMate 3.2)
2. Export: **File → Export → Open Exchange XML** → `exchange/`
3. Run `make import` to generate parsed JSON for AI agents
4. Commit both the XML export and generated files

## Relationship to other repos

| Repo | Contains |
|------|----------|
| `banxe-architecture` | System architecture (ApplicationComponent, TechnologyService) |
| `banxe-business-processes` | Business layer (BusinessProcess, BusinessRole, BusinessActor) |
| `banxe-emi-stack` | Implementation (Python code, API, tests) |
