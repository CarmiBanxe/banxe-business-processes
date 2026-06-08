#!/usr/bin/env python3
"""Generate process/actor scaffolding from ArchiMate AND emit the process registry.

Two responsibilities:

1. SCAFFOLD (non-destructive) — for every BusinessProcess in the parsed ArchiMate
   model, ensure a base process YAML exists under processes/<domain>/<slug>.yaml,
   and ensure each actor YAML exists. Existing files are NEVER overwritten, so the
   resolvability enrichment (process_id, version, steps, triggers, actors,
   compliance_refs — see scripts/enrich_processes.py) and ArchiMate fields are
   preserved. `make import` is therefore safe to re-run with no data loss.

2. REGISTRY (deterministic) — scan every processes/**/*.yaml (ArchiMate-derived
   AND manually-authored stubs) and emit ai-agent-context/processes-registry.json:
   one entry per process as {process_id, version, domain, name, summary, actors,
   triggers, stub}. Each entry's {process_id, version} is validated against
   ai-agent-context/process_ref.schema.json (the ADR-048 D3 / ADR-049 D2
   process_ref contract). This is the L1->process_ref resolution target.

Run from the repo root: `python3 scripts/generate_from_archimate.py` (or `make import`).
"""
import glob
import json
import os
import re

import yaml
from jsonschema import Draft7Validator

ARCH_DIR = os.path.expanduser('~/banxe-architecture/archimate/parsed')
REGISTRY_PATH = 'ai-agent-context/processes-registry.json'
SCHEMA_PATH = 'ai-agent-context/process_ref.schema.json'

DOMAIN_MAP = {
    'Customer Onboarding': 'onboarding',
    'Sanctions Screening': 'compliance',
    'Transaction Monitoring': 'compliance',
    'SAR Filing': 'compliance',
    'Consumer Duty DISP': 'compliance',
    'Payment Processing': 'payments',
    'Daily Reconciliation': 'treasury',
    'FIN060 Return': 'treasury',
    'Card Issuance': 'card-lifecycle',
    'Card Activation': 'card-lifecycle',
    'Card Blocking': 'card-lifecycle',
    'Card Replacement': 'card-lifecycle',
    'Risk Assessment': 'risk',
    'Operational Risk Monitoring': 'risk',
    'Fraud Detection': 'risk',
    'OKR Planning': 'strategy',
    'Regulatory Horizon Scanning': 'strategy',
    'Product Roadmap Review': 'strategy',
    'BaaS Tenant Onboarding': 'baas',
    'BaaS SLA Monitoring': 'baas',
    'BaaS Settlement': 'baas',
}

ACTOR_ROLES = {
    'CEO': ('strategy', 'Chief Executive Officer'),
    'MLRO': ('compliance', 'Money Laundering Reporting Officer'),
    'Compliance Officer': ('compliance', 'Ensures regulatory compliance'),
    'KYC Analyst': ('onboarding', 'Customer due diligence and identity verification'),
    'Payment Operations': ('payments', 'Payment processing and settlement'),
    'Treasury Manager': ('treasury', 'Safeguarding accounts and FCA reporting'),
    'Risk Manager': ('risk', 'Operational and financial risk management'),
    'Customer Support': ('onboarding', 'Customer queries and Consumer Duty DISP'),
    'CTIO': ('strategy', 'Chief Technology and Innovation Officer'),
    'Card Operations': ('card-lifecycle', 'Card issuance activation and blocking'),
    'BaaS Partner Manager': ('baas', 'BaaS tenant onboarding and SLAs'),
}


def slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def scaffold():
    """Create any missing base process/actor YAML from ArchiMate. Never overwrites."""
    with open(f'{ARCH_DIR}/elements.json') as f:
        elements = json.load(f)
    with open(f'{ARCH_DIR}/relations.json') as f:
        relations = json.load(f)

    created = 0
    for elem in elements:
        if elem.get('type') != 'BusinessProcess':
            continue
        name = elem['name']
        slug = slugify(name)
        domain = DOMAIN_MAP.get(name, 'strategy')
        proc_dir = f'processes/{domain}'
        path = f'{proc_dir}/{slug}.yaml'
        if os.path.exists(path):
            continue  # preserve enrichment — never overwrite
        os.makedirs(proc_dir, exist_ok=True)
        eid = elem['id']
        related = []
        for r in relations:
            if r.get('source') == eid or r.get('target') == eid:
                oid = r['target'] if r['source'] == eid else r['source']
                other = next((e for e in elements if e['id'] == oid), None)
                if other:
                    related.append((other['name'], other['type'], r['type']))
        doc = elem.get('documentation', '')
        lines = [f'# {name}', f'archimate_id: {eid}', 'type: BusinessProcess',
                 f'domain: {domain}', f'name: {name}']
        if doc:
            lines.append('documentation: |')
            lines.append(f'  {doc}')
        if related:
            lines.append('relationships:')
            for rn, rt, rr in related:
                lines.append(f'  - name: {rn}')
                lines.append(f'    type: {rt}')
                lines.append(f'    relation: {rr}')
        with open(path, 'w') as f:
            f.write(chr(10).join(lines) + chr(10))
        created += 1
        print(f'  NEW {path}')

    os.makedirs('actors', exist_ok=True)
    for role, (domain, desc) in ACTOR_ROLES.items():
        slug = slugify(role)
        path = f'actors/{slug}.yaml'
        if os.path.exists(path):
            continue
        lines = [f'# {role}', 'type: BusinessActor', f'domain: {domain}',
                 f'name: {role}', f'description: {desc}']
        with open(path, 'w') as f:
            f.write(chr(10).join(lines) + chr(10))
        created += 1
        print(f'  NEW {path}')
    print(f'Scaffold: {created} file(s) created, existing files preserved.')


def summarise(doc: str) -> str:
    """First sentence/line of the documentation as a one-line summary."""
    text = ' '.join((doc or '').split())
    if not text:
        return ''
    return text.split('. ')[0].rstrip('.').strip()


def build_registry() -> dict:
    """Scan all process YAMLs and build the deterministic registry."""
    entries = []
    for path in sorted(glob.glob('processes/**/*.yaml', recursive=True)):
        with open(path) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or 'process_id' not in data:
            raise ValueError(f'{path}: missing process_id (run scripts/enrich_processes.py)')
        entries.append({
            'process_id': data['process_id'],
            'version': str(data['version']),
            'domain': data.get('domain', ''),
            'name': data.get('name', ''),
            'summary': summarise(data.get('documentation', '')),
            'actors': data.get('actors', []),
            'triggers': data.get('triggers', []),
            'stub': bool(data.get('stub', False)),
        })
    entries.sort(key=lambda e: e['process_id'])
    return {
        'schema': 'ai-agent-context/process_ref.schema.json',
        'description': 'S13-00 Business Process Repository registry — L1 intent->process_ref '
                       'resolution target (ADR-048 D3 / ADR-049 D2). process_ref = {process_id, version}.',
        'count': len(entries),
        'processes': entries,
    }


def write_registry(registry: dict):
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    for entry in registry['processes']:
        ref = {'process_id': entry['process_id'], 'version': entry['version']}
        errs = sorted(validator.iter_errors(ref), key=str)
        if errs:
            raise ValueError(f"{ref}: invalid process_ref — {errs[0].message}")
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(f'Registry: {registry["count"]} processes -> {REGISTRY_PATH} '
          f'(all process_ref entries valid).')


def main():
    if os.path.isdir(ARCH_DIR):
        scaffold()
    else:
        print(f'  (ArchiMate dir {ARCH_DIR} absent — skipping scaffold, building registry only)')
    registry = build_registry()
    write_registry(registry)


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
