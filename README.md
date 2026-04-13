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
└── .claude/                ← Claude Code configuration
```

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
