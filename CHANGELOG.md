# Changelog — banxe-business-processes

## Unreleased — BPR Resolvable (audit gap #3, Sprint S3)

Made the S13-00 Business Process Repository **resolvable** per ADR-048 (Business
Process Repository) and ADR-049 (Intent Layer). The IL anchor for this milestone is
recorded separately in `banxe-architecture`.

Added (no ArchiMate data lost — all changes additive):

- **Process enrichment** — every `processes/**/*.yaml` now carries `process_id`,
  `version`, `triggers`, `steps`, `actors`, `compliance_refs` **in addition to** its
  existing ArchiMate fields (`archimate_id`, `type`, `domain`, `name`, `documentation`,
  `relationships`). Applied in place by `scripts/enrich_processes.py`.
- **Registry** — `ai-agent-context/processes-registry.json`, the L1 → `process_ref`
  lookup target, generated deterministically by `scripts/generate_from_archimate.py`
  and validated against the `process_ref = {process_id, version}` contract.
- **Intent map** — `ai-agent-context/intent-process-map.yaml`, the L1 intent →
  `process_id(s)` resolution table. All 9 client-facing capabilities resolve.
- **process_ref schema** — `ai-agent-context/process_ref.schema.json` (local mirror of
  the ADR-048 D3 contract; the canonical schema is not yet authored in
  `banxe-architecture`).
- **Validation proof** — `scripts/validate_resolvable.py` + `bpr-validate` CI workflow
  assert every `process_ref`, intent target, and actor link resolves.
- **Stub processes** for client capabilities not yet in ArchiMate (documented as stubs,
  TODO manual enrichment): `fx/fx-exchange`, `wallet/wallet-balance-inquiry`,
  `statements/statement-generation`, `analytics/spending-analytics`,
  `crm/referral-management`, `notifications/notification-dispatch`.

`scripts/generate_from_archimate.py` is now **non-destructive**: it never overwrites an
existing process/actor file, so `make import` preserves enrichment.
