#!/usr/bin/env bash
# =============================================================================
# End-to-End Test Script
# =============================================================================
# Exercises CLI model override, duration tracking, and manifest assembly.
# Requires the 'fepo' Anaconda environment.
#
# Usage:
#   bash scripts/test_e2e.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate fepo

echo "========================================"
echo "  FEPO E2E Test Suite"
echo "========================================"
echo "  Python: $(python --version)"
echo "  Working dir: $PROJECT_ROOT"
echo "========================================"
echo ""

# --- Unit tests for new modules ---

echo "==> Running CLI model override tests..."
python -m pytest tests/test_cli_model_override.py -v --tb=short

echo ""
echo "==> Running duration tracking tests..."
python -m pytest tests/test_duration_tracking.py -v --tb=short

echo ""
echo "==> Running experiment manifest tests..."
python -m pytest tests/test_experiment_manifest.py -v --tb=short

# --- Verify existing tests still pass ---

echo ""
echo "==> Running full test suite (non-integration)..."
python -m pytest tests/ -v --tb=short

echo ""
echo "========================================"
echo "  All E2E tests passed."
echo "========================================"
