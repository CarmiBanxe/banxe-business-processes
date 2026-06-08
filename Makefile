# Makefile - banxe-business-processes
.PHONY: import generate registry validate clean help

PYTHON := python3
GENERATE := scripts/generate_from_archimate.py
VALIDATE := scripts/validate_resolvable.py

import: generate
	@echo "Import complete"

generate:
	@echo "Generating processes + actors from ArchiMate + registry..."
	$(PYTHON) $(GENERATE)

# Alias: rebuild the registry (generate is non-destructive — never overwrites enrichment)
registry: generate

validate: registry
	@echo "Validating BPR resolvability (process_ref + intent map + actors)..."
	$(PYTHON) $(VALIDATE)

clean:
	@echo "Cleaning generated YAML files..."
	find processes/ -name "*.yaml" -delete
	find actors/ -name "*.yaml" -delete

help:
	@echo "  make import   - Scaffold (non-destructive) + rebuild the process registry"
	@echo "  make registry - Rebuild ai-agent-context/processes-registry.json"
	@echo "  make validate - Assert every process_ref + intent + actor resolves"
	@echo "  make clean    - Remove generated YAML files"
