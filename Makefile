# Makefile - banxe-business-processes
.PHONY: import generate clean help

PYTHON := python3
GENERATE := scripts/generate_from_archimate.py

import: generate
	@echo "Import complete"

generate:
	@echo "Generating processes + actors from ArchiMate..."
	$(PYTHON) $(GENERATE)

clean:
	@echo "Cleaning generated YAML files..."
	find processes/ -name "*.yaml" -delete
	find actors/ -name "*.yaml" -delete

help:
	@echo "  make import  - Generate process + actor YAML from ArchiMate"
	@echo "  make clean   - Remove generated YAML files"
