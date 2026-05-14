.PHONY: lint test check-headers check-tenant-docs check-safety fix-headers fix_license ci

# Use bash with globstar for recursive globbing.
SHELL:=/bin/bash -O globstar -O dotglob

# ── Checks (read-only) ─────────────────────────────────────────────

lint:
	python -m ruff check .

test:
	python -m pytest

check-headers:
	python scripts/check_license_headers.py

check-tenant-docs:
	python scripts/check_tenant_docs.py

check-safety:  ## Local-only (script is gitignored — contains internal references)
	python scripts/check_oss_safety.py

ci: lint check-headers check-tenant-docs test

# ── Fixes (mutating) ───────────────────────────────────────────────

fix_license:
	docker run --rm --volume $(shell pwd):/data fsfe/reuse annotate \
		--copyright-prefix string \
		--copyright "Cisco Systems, Inc. and its affiliates" \
		-l "Apache-2.0" \
		$$(shopt -s globstar dotglob; \
		   for f in **/*.{py,md}; do \
		   [[ "$$f" == .venv/* || "$$f" == .direnv/* ]] && continue; \
		     printf '%s\n' "$$f"; \
		   done)

fix-headers: fix_license
