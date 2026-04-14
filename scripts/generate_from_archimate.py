#!/usr/bin/env python3
import json, os, re

ARCH_DIR = os.path.expanduser('~/banxe-architecture/archimate/parsed')

with open(f'{ARCH_DIR}/elements.json') as f:
    elements = json.load(f)

with open(f'{ARCH_DIR}/relations.json') as f:
    relations = json.load(f)

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

for elem in elements:
    if elem.get('type') == 'BusinessProcess':
        name = elem['name']
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        domain = DOMAIN_MAP.get(name, 'strategy')
        proc_dir = f'processes/{domain}'
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
        lines = [f'# {name}', f'archimate_id: {eid}', f'type: BusinessProcess', f'domain: {domain}', f'name: {name}']
        if doc:
            lines.append(f'documentation: |')
            lines.append(f'  {doc}')
        if related:
            lines.append('relationships:')
            for rn, rt, rr in related:
                lines.append(f'  - name: {rn}')
                lines.append(f'    type: {rt}')
                lines.append(f'    relation: {rr}')
        path = f'{proc_dir}/{slug}.yaml'
        with open(path, 'w') as f:
            f.write(chr(10).join(lines) + chr(10))
        print(f'  OK {path}')

os.makedirs('actors', exist_ok=True)
for role, (domain, desc) in ACTOR_ROLES.items():
    slug = re.sub(r'[^a-z0-9]+', '-', role.lower()).strip('-')
    lines = [f'# {role}', f'type: BusinessActor', f'domain: {domain}', f'name: {role}', f'description: {desc}']
    with open(f'actors/{slug}.yaml', 'w') as f:
        f.write(chr(10).join(lines) + chr(10))
    print(f'  OK actors/{slug}.yaml')

bp = sum(1 for e in elements if e.get('type') == 'BusinessProcess')
print(f'Done: {bp} processes, {len(ACTOR_ROLES)} actors')
