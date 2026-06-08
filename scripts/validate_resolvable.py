#!/usr/bin/env python3
"""Validation proof — the S13-00 Business Process Repository is RESOLVABLE.

Asserts the intent->process_ref resolution chain holds end to end:

  1. Every entry in ai-agent-context/processes-registry.json is a valid process_ref
     ({process_id, version}) against ai-agent-context/process_ref.schema.json.
  2. process_id values are unique.
  3. Every process_id referenced by ai-agent-context/intent-process-map.yaml exists
     in the registry (no intent resolves to a missing process).
  4. Every actor referenced by a registry entry exists as actors/<id>.yaml.

Exits non-zero on any failure (CI-friendly). Reports pass counts.

Run from the repo root: `python3 scripts/validate_resolvable.py`.
"""
import json
import os
import sys

import yaml
from jsonschema import Draft7Validator

REGISTRY_PATH = 'ai-agent-context/processes-registry.json'
SCHEMA_PATH = 'ai-agent-context/process_ref.schema.json'
INTENT_MAP_PATH = 'ai-agent-context/intent-process-map.yaml'


def main() -> int:
    failures = []

    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    with open(INTENT_MAP_PATH) as f:
        intent_map = yaml.safe_load(f)

    validator = Draft7Validator(schema)
    process_ids = set()
    ref_pass = 0

    # 1 + 2 — every registry entry is a valid, unique process_ref
    for entry in registry['processes']:
        ref = {'process_id': entry['process_id'], 'version': entry['version']}
        errs = sorted(validator.iter_errors(ref), key=str)
        if errs:
            failures.append(f"registry: {ref} invalid process_ref — {errs[0].message}")
            continue
        if entry['process_id'] in process_ids:
            failures.append(f"registry: duplicate process_id {entry['process_id']}")
            continue
        process_ids.add(entry['process_id'])
        ref_pass += 1

    # 4 — every referenced actor exists
    actor_refs = 0
    actor_pass = 0
    for entry in registry['processes']:
        for actor in entry.get('actors', []):
            actor_refs += 1
            if os.path.exists(f'actors/{actor}.yaml'):
                actor_pass += 1
            else:
                failures.append(f"registry: {entry['process_id']} references missing actor '{actor}'")

    # 3 — every intent resolves to an existing process_id
    intent_pass = 0
    intent_total = 0
    resolved_caps = set()
    for item in intent_map['intents']:
        intent_total += 1
        targets = item.get('process_ids', [])
        if not targets:
            failures.append(f"intent-map: intent '{item['intent']}' has no process_ids")
            continue
        missing = [pid for pid in targets if pid not in process_ids]
        if missing:
            failures.append(f"intent-map: intent '{item['intent']}' -> missing process_id(s) {missing}")
            continue
        intent_pass += 1
        resolved_caps.add(item.get('capability', item['intent']))

    print("=" * 60)
    print("BPR RESOLVABILITY VALIDATION")
    print("=" * 60)
    print(f"  process_ref entries valid : {ref_pass}/{len(registry['processes'])}")
    print(f"  unique process_ids        : {len(process_ids)}")
    print(f"  actor references resolved : {actor_pass}/{actor_refs}")
    print(f"  intents resolved          : {intent_pass}/{intent_total}")
    print(f"  distinct capabilities      : {len(resolved_caps)}")
    print("=" * 60)

    if failures:
        print(f"FAIL — {len(failures)} problem(s):")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print(f"PASS — {ref_pass} process_refs valid, "
          f"{intent_pass} intents resolvable, {actor_pass} actor links resolved.")
    return 0


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(main())
