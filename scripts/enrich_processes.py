#!/usr/bin/env python3
"""Additive, in-place enrichment of process YAMLs (audit gap #3 — S3).

Adds the resolvability fields required by ADR-048 (Business Process Repository)
and ADR-049 (Intent Layer) WITHOUT removing any existing ArchiMate field:

    process_id      stable handle, derived from archimate_id (strip 'id-' prefix)
    version         semantic version; "1.0.0" initial
    triggers        what initiates the process
    steps           ordered activity list (derived from documentation + relationships)
    actors          links to actors/<id>.yaml by responsibility
    compliance_refs ADR / regulation / policy ids where evident, else []

The transform is text-append only: existing lines (comment header, archimate_id,
type, domain, name, documentation, relationships) are preserved verbatim. The
script is idempotent — a file that already carries `process_id:` is skipped.

Enrichment content is keyed by archimate_id so it stays bound to the ArchiMate
source of truth. Run once from the repo root: `python3 scripts/enrich_processes.py`.
"""
import glob
import os

# archimate_id -> enrichment block. process_id is derived (strip 'id-' prefix).
ENRICHMENT = {
    "id-baas-settlement": {
        "triggers": ["Scheduled — daily settlement window per tenant agreement"],
        "steps": [
            "Aggregate the tenant's transactions for the settlement window",
            "Calculate fees due",
            "Compute revenue share",
            "Reconcile against the ledger",
            "Post the settlement to the tenant account",
        ],
        "actors": ["baas-partner-manager", "treasury-manager", "payment-operations"],
        "compliance_refs": [],
    },
    "id-baas-sla": {
        "triggers": ["Continuous — real-time metric ingestion; threshold-breach alerts"],
        "steps": [
            "Collect uptime, latency and error-rate metrics",
            "Evaluate metrics against the tenant SLA thresholds",
            "Raise a breach alert when a threshold is crossed",
            "Report SLA status to the tenant",
        ],
        "actors": ["baas-partner-manager", "ctio"],
        "compliance_refs": [],
    },
    "id-baas-onboarding": {
        "triggers": ["Tenant signs the BaaS partner agreement"],
        "steps": [
            "Run KYB / due diligence on the prospective tenant",
            "Provision a sandbox environment",
            "Issue API keys",
            "Configure webhooks",
            "Promote the tenant to production",
        ],
        "actors": ["baas-partner-manager", "compliance-officer", "kyc-analyst"],
        "compliance_refs": ["MLR-2017"],
    },
    "id-card-activation": {
        "triggers": ["Customer initiates activation via app or IVR"],
        "steps": [
            "Authenticate the customer",
            "Verify card ownership",
            "Activate the card",
            "Enrol the card in 3DS",
            "Confirm activation to the customer",
        ],
        "actors": ["card-operations", "customer-support"],
        "compliance_refs": ["PCI-DSS"],
    },
    "id-card-blocking": {
        "triggers": [
            "Customer reports the card lost/stolen or requests a freeze",
            "Fraud-detection signal",
        ],
        "steps": [
            "Receive the block/freeze request",
            "Authenticate the request source",
            "Block the card in real time via the Hyperswitch API",
            "Confirm the block to the customer",
            "Log the event for fraud review",
        ],
        "actors": ["card-operations", "customer-support", "risk-manager"],
        "compliance_refs": ["PCI-DSS"],
    },
    "id-card-issuance": {
        "triggers": ["An approved customer requests a card"],
        "steps": [
            "Validate customer eligibility",
            "Create the card in the Hyperswitch Card Vault",
            "Provision the PAN (PCI DSS scope)",
            "Deliver the virtual or physical card",
        ],
        "actors": ["card-operations"],
        "compliance_refs": ["PCI-DSS"],
    },
    "id-card-replacement": {
        "triggers": ["Card reported lost/stolen, damaged, or expiring"],
        "steps": [
            "Block the old card",
            "Issue a new PAN via the Card Vault",
            "Migrate recurring mandates to the new PAN",
            "Deliver the replacement card",
        ],
        "actors": ["card-operations", "customer-support"],
        "compliance_refs": ["PCI-DSS"],
    },
    "id-consumer-duty-process": {
        "triggers": ["Customer complaint received"],
        "steps": [
            "Log the complaint",
            "Acknowledge within 3 business days",
            "Investigate the complaint",
            "Resolve within the 8-week SLA",
            "Issue the final response",
            "Escalate to the FCA / FOS where unresolved",
        ],
        "actors": ["compliance-officer", "customer-support"],
        "compliance_refs": ["FCA-DISP", "PS22/9", "Consumer-Duty"],
    },
    "id-sanctions-screening-process": {
        "triggers": [
            "Customer onboarding",
            "Each inbound/outbound payment",
        ],
        "steps": [
            "Extract the party data to screen",
            "Screen against OFAC / UN / EU / UK sanctions lists",
            "Run the PEP check",
            "Evaluate potential matches",
            "Escalate confirmed hits to the MLRO",
        ],
        "actors": ["compliance-officer", "mlro"],
        "compliance_refs": ["MLR-2017-Reg.28"],
    },
    "id-sar-process": {
        "triggers": ["Suspicious activity detected or flagged"],
        "steps": [
            "Draft the Suspicious Activity Report",
            "MLRO review",
            "MLRO approval",
            "Submit to the NCA",
            "Retain records",
        ],
        "actors": ["mlro", "compliance-officer"],
        "compliance_refs": ["POCA-2002-s.330"],
    },
    "id-tx-monitoring-process": {
        "triggers": ["Each transaction event (real-time)"],
        "steps": [
            "Ingest the transaction",
            "Score it via the Jube probabilistic ML engine",
            "Evaluate against monitoring rules",
            "Raise an alert when a threshold is crossed",
            "Route the alert to case management",
        ],
        "actors": ["mlro", "compliance-officer", "risk-manager"],
        "compliance_refs": ["PSR-APP-2024", "MLR-2017"],
    },
    "id-onboarding-process": {
        "triggers": ["Prospective customer begins sign-up"],
        "steps": [
            "Capture customer details",
            "Run KYC identity verification",
            "Risk-assess the customer",
            "Accept or decline",
            "Create the account",
            "Execute the customer agreement",
        ],
        "actors": ["kyc-analyst", "compliance-officer", "customer-support"],
        "compliance_refs": ["EMR-2011-Reg.4", "MLR-2017"],
    },
    "id-payment-processing-process": {
        "triggers": ["Customer initiates a payment or transfer"],
        "steps": [
            "Initiate the payment",
            "Sanctions / AML screen",
            "Authorise the payment",
            "Settle via the FPS/SEPA rail",
            "Notify the customer",
        ],
        "actors": ["payment-operations", "compliance-officer"],
        "compliance_refs": ["PSR-2017"],
    },
    "id-fraud-detection": {
        "triggers": ["Each transaction / authorisation event (real-time)"],
        "steps": [
            "Ingest the event",
            "Score fraud risk via the Jube ML engine",
            "Evaluate against the threshold",
            "Block or hold suspicious activity",
            "Route to investigation",
        ],
        "actors": ["risk-manager", "mlro"],
        "compliance_refs": ["PSR-APP-2024"],
    },
    "id-ops-risk-monitoring": {
        "triggers": ["Scheduled — daily key-risk-indicator evaluation"],
        "steps": [
            "Collect key risk indicators",
            "Compare against risk-appetite thresholds",
            "Flag breaches",
            "Escalate to the risk owner",
            "Report",
        ],
        "actors": ["risk-manager", "ctio"],
        "compliance_refs": ["Basel-III-Pillar-2"],
    },
    "id-risk-assessment": {
        "triggers": ["Customer onboarding", "Periodic risk review"],
        "steps": [
            "Gather customer risk factors",
            "Compute the risk score",
            "Assign the CDD/EDD tier",
            "Set the ongoing monitoring level",
        ],
        "actors": ["risk-manager", "kyc-analyst"],
        "compliance_refs": ["MLR-2017-Reg.28"],
    },
    "id-okr-planning": {
        "triggers": ["Quarterly planning cycle"],
        "steps": [
            "CEO sets company OKRs",
            "Teams derive their key results",
            "Align objectives across teams",
            "Mid-quarter review",
            "Score at quarter end",
        ],
        "actors": ["ceo", "ctio"],
        "compliance_refs": [],
    },
    "id-roadmap-review": {
        "triggers": ["Monthly product-review cadence"],
        "steps": [
            "Collect candidate features",
            "Assess each against compliance deadlines",
            "Prioritise",
            "Update the roadmap",
        ],
        "actors": ["ctio", "ceo"],
        "compliance_refs": [],
    },
    "id-horizon-scanning": {
        "triggers": ["New FCA/PRA/EBA publication", "Scheduled horizon review"],
        "steps": [
            "Monitor regulatory feeds",
            "Identify relevant changes",
            "Assess impact",
            "Assign an owner",
            "Track through to implementation",
        ],
        "actors": ["compliance-officer", "mlro", "ceo"],
        "compliance_refs": [],
    },
    "id-daily-recon-process": {
        "triggers": ["Scheduled — cron at 23:50 UTC daily"],
        "steps": [
            "Load internal (Midaz) balances",
            "Load external (CAMT.053) statements",
            "Match internal vs external",
            "Identify reconciliation breaks",
            "Investigate and resolve breaks",
            "Sign off the reconciliation",
        ],
        "actors": ["treasury-manager", "payment-operations"],
        "compliance_refs": ["CASS-7.15.17R"],
    },
    "id-fin060-process": {
        "triggers": ["Annual FCA reporting deadline"],
        "steps": [
            "Aggregate safeguarding data",
            "Prepare the FIN060 return",
            "Internal review",
            "Submit via RegData",
        ],
        "actors": ["treasury-manager", "compliance-officer"],
        "compliance_refs": ["FCA-FIN060", "CASS"],
    },
}

VERSION_INITIAL = "1.0.0"


def to_process_id(archimate_id: str) -> str:
    """Stable process_id derived from archimate_id by stripping the 'id-' prefix."""
    return archimate_id[3:] if archimate_id.startswith("id-") else archimate_id


def yaml_list(key: str, items: list, quote: bool = False) -> list:
    lines = [f"{key}:"]
    if not items:
        return [f"{key}: []"]
    for it in items:
        val = f'"{it}"' if quote else it
        lines.append(f"  - {val}")
    return lines


def read_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def enrich_file(path: str) -> str:
    with open(path) as f:
        text = f.read()
    if "process_id:" in text:
        return "skip"
    archimate_id = read_field(text, "archimate_id")
    data = ENRICHMENT.get(archimate_id)
    if data is None:
        return f"NO-DATA ({archimate_id})"
    process_id = to_process_id(archimate_id)
    block = ["", f"process_id: {process_id}", f'version: "{VERSION_INITIAL}"']
    block += yaml_list("triggers", data["triggers"], quote=True)
    block += yaml_list("steps", data["steps"], quote=True)
    block += yaml_list("actors", data["actors"])
    block += yaml_list("compliance_refs", data["compliance_refs"], quote=True)
    if not text.endswith("\n"):
        text += "\n"
    with open(path, "w") as f:
        f.write(text + "\n".join(block) + "\n")
    return "OK"


def main() -> None:
    files = sorted(glob.glob("processes/**/*.yaml", recursive=True))
    counts = {"OK": 0, "skip": 0, "other": 0}
    for path in files:
        result = enrich_file(path)
        if result == "OK":
            counts["OK"] += 1
        elif result == "skip":
            counts["skip"] += 1
        else:
            counts["other"] += 1
            print(f"  WARN {path}: {result}")
        print(f"  {result:8} {path}")
    print(f"Enriched: {counts['OK']}, skipped: {counts['skip']}, warnings: {counts['other']}")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
