#!/usr/bin/env bash
# =============================================================================
# Optimization Loop Script
# =============================================================================
# Invokes the optimization agent in a loop, relaunching fresh sessions until
# the goal is met or max rounds are exhausted. Each round is a fresh `claude`
# invocation; the agent persists state via iteration-memory.jsonl.
#
# Usage:
#   scripts/optimize-loop.sh --tenant <id> [--goal "description"] [--max-rounds N] [--dry-run]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common functions
source "$PROJECT_ROOT/deploy/scripts/common.sh"

# =============================================================================
# Defaults
# =============================================================================

TENANT_ID=""
GOAL=""
MAX_ROUNDS=10
DRY_RUN=false
TASK_MODEL="gpt-4.1-mini"
LOCAL_EVAL=false

# =============================================================================
# Help
# =============================================================================

show_help() {
    cat << 'EOF'
Optimization Loop Script

Invokes the optimization agent repeatedly until the goal is met or max rounds
are exhausted. Each round is a fresh claude session; the agent recovers state
from iteration-memory.jsonl.

USAGE:
    scripts/optimize-loop.sh --tenant <id> [options]

REQUIRED:
    --tenant TENANT_ID      Tenant to optimize

OPTIONS:
    --goal "description"    Goal/success criteria passed to agent (free text)
    --max-rounds N          Max loop iterations (default: 10)
    --task-model MODEL      Task model for manifest reporting (default: gpt-4.1-mini)
    --local                 Run evals locally instead of on K8s (no GCS/GKE auth required)
    --dry-run               Print first-round command without executing
    -h, --help              Show this help

EXAMPLES:
    # Basic optimization loop
    scripts/optimize-loop.sh --tenant hotpotqa

    # With a specific goal and max rounds
    scripts/optimize-loop.sh --tenant hotpotqa --goal "reach 80% accuracy" --max-rounds 5

    # Dry run to inspect the generated command
    scripts/optimize-loop.sh --tenant hotpotqa --dry-run

EOF
}

# =============================================================================
# Arg Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --tenant)
            if [[ $# -lt 2 ]]; then
                log_error "--tenant requires a tenant ID"
                exit 1
            fi
            TENANT_ID="$2"
            shift 2
            ;;
        --goal)
            if [[ $# -lt 2 ]]; then
                log_error "--goal requires a description"
                exit 1
            fi
            GOAL="$2"
            shift 2
            ;;
        --max-rounds)
            if [[ $# -lt 2 ]]; then
                log_error "--max-rounds requires a number"
                exit 1
            fi
            MAX_ROUNDS="$2"
            if ! [[ "$MAX_ROUNDS" =~ ^[0-9]+$ ]]; then
                log_error "--max-rounds must be a positive integer: $MAX_ROUNDS"
                exit 1
            fi
            shift 2
            ;;
        --task-model)
            if [[ $# -lt 2 ]]; then
                log_error "--task-model requires a model name"
                exit 1
            fi
            TASK_MODEL="$2"
            shift 2
            ;;
        --local)
            LOCAL_EVAL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# =============================================================================
# Validation
# =============================================================================

if [ -z "$TENANT_ID" ]; then
    log_error "--tenant is required"
    show_help
    exit 1
fi

validate_tenant_id "$TENANT_ID"

if [ ! -d "$PROJECT_ROOT/tenants/$TENANT_ID" ]; then
    log_error "Tenant directory not found: tenants/$TENANT_ID"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    log_error "claude CLI not found. Install it first."
    exit 1
fi

# Auto-derive goal from playbook Stop Criteria if --goal was not specified
if [ -z "$GOAL" ]; then
    PLAYBOOK="$PROJECT_ROOT/tenants/$TENANT_ID/docs/iteration-playbook.md"
    if [ -f "$PLAYBOOK" ]; then
        GOAL=$(awk '/^## Stop Criteria/{found=1; next} found && /^- /{sub(/^- /, ""); print; exit}' "$PLAYBOOK")
    fi
fi

# =============================================================================
# Environment
# =============================================================================

source_envrc() {
    local file="$1"
    if [ -f "$file" ]; then
        # Only source export statements — ignore direnv builtins and other commands
        set -a
        eval "$(grep -E '^\s*export\s+' "$file")" 2>/dev/null || true
        set +a
    fi
}

# Source .envrc from the main worktree (resolves via git), then the local one
MAIN_WORKTREE="$(git -C "$PROJECT_ROOT" worktree list --porcelain 2>/dev/null | head -1 | sed 's/^worktree //')"
if [ -n "$MAIN_WORKTREE" ]; then
    source_envrc "$MAIN_WORKTREE/.envrc"
fi
source_envrc "$PROJECT_ROOT/.envrc"

# Suppress all Google Cloud SDK interactive prompts (auth, consent, surveys)
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

# =============================================================================
# Log Directory
# =============================================================================

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="$PROJECT_ROOT/local-results/optimize-loops/${TENANT_ID}-${TIMESTAMP}"
PROGRESS_LOG="$LOG_DIR/progress.log"

# =============================================================================
# Prompts
# =============================================================================

if [ "$LOCAL_EVAL" = true ]; then
    EVAL_INSTRUCTION="Run all evals LOCALLY with: python -m hephaestus.cli eval --config <config>. Do NOT use K8s or deploy/scripts/run_eval.sh. Do NOT use gsutil or any GCS commands."
else
    EVAL_INSTRUCTION="Use K8s for all eval runs (deploy/scripts/run_eval.sh --config <config> --detach). NEVER run evals locally."
fi

INITIAL_PROMPT="Optimize eval quality for tenant \"${TENANT_ID}\".
${GOAL:+Goal: ${GOAL}}

${EVAL_INSTRUCTION}"

CONTINUE_PROMPT="Continue optimizing tenant \"${TENANT_ID}\". Your previous round ended (likely context or turn limit).
${GOAL:+Goal: ${GOAL}}
Read iteration-memory.jsonl to recover state. Pick up where you left off.

${EVAL_INSTRUCTION}"

STATUS_INSTRUCTIONS='IMPORTANT: At the END of your response, you MUST emit exactly one of these XML tags:
- <optimization_status>requirements met</optimization_status> if the optimization goal has been met or all allowed levels are exhausted
- <optimization_status>requirements not met</optimization_status> if there is more work to do

Always emit this tag, even if you encountered an error. This is machine-parsed.'

# =============================================================================
# Loop
# =============================================================================

EXPERIMENT_START=$(date -Iseconds)
EXPERIMENT_START_EPOCH=$(date +%s)

echo ""
echo "========================================"
echo "  Optimization Loop"
echo "========================================"
echo "  Tenant:     $TENANT_ID"
echo "  Task model: $TASK_MODEL"
echo "  Eval mode:  $([ "$LOCAL_EVAL" = true ] && echo "LOCAL" || echo "K8s")"
echo "  Goal:       ${GOAL:-<none>}"
echo "  Max rounds: $MAX_ROUNDS"
echo "  Log dir:    $LOG_DIR"
echo "========================================"
echo ""

error_streak=0
MAX_ERRORS=3

for (( round=1; round<=MAX_ROUNDS; round++ )); do
    log_step "Round $round / $MAX_ROUNDS"

    # Pick prompt
    if [ "$round" -eq 1 ]; then
        PROMPT="$INITIAL_PROMPT"
    else
        PROMPT="$CONTINUE_PROMPT"
    fi

    ROUND_FILE="$LOG_DIR/round-$(printf '%03d' "$round").json"

    # Build command
    CLAUDE_CMD=(
        claude -p "$PROMPT"
        --agent optimization
        --output-format stream-json
        --verbose
        --effort high
        --dangerously-skip-permissions
        --append-system-prompt "$STATUS_INSTRUCTIONS"
    )

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would execute:"
        echo "  ${CLAUDE_CMD[*]}"
        echo "  > $ROUND_FILE"
        exit 0
    fi

    # Create log dir on first real execution
    mkdir -p "$LOG_DIR"

    # Execute: stream-json streams events to stdout in real time.
    # tee saves to file while stream-filter.py shows intermediate steps in the terminal.
    log_info "Launching claude agent..."
    local_exit=0
    STDERR_FILE="$LOG_DIR/round-$(printf '%03d' "$round").stderr"
    set +eo pipefail
    "${CLAUDE_CMD[@]}" 2>"$STDERR_FILE" \
        | tee "$ROUND_FILE" \
        | python3 -u "$SCRIPT_DIR/stream-filter.py"
    local_exit=${PIPESTATUS[0]}
    set -eo pipefail

    if [ "$local_exit" -ne 0 ]; then
        error_streak=$((error_streak + 1))
        log_warn "claude exited with code $local_exit (error streak: $error_streak/$MAX_ERRORS)"
        echo "$(date -Iseconds) round=$round status=error exit_code=$local_exit" >> "$PROGRESS_LOG"

        if [ "$error_streak" -ge "$MAX_ERRORS" ]; then
            log_error "Aborting after $MAX_ERRORS consecutive errors."
            log_info "Last round output: $ROUND_FILE"
            log_info "Progress log: $PROGRESS_LOG"
            exit 1
        fi
        continue
    fi

    # Reset error streak on success
    error_streak=0

    # Extract status tag from the stream-json output (last 'result' event)
    STATUS_VALUE=$(python3 -c "
import json, re, sys
for line in reversed(open(sys.argv[1]).readlines()):
    line = line.strip()
    if not line:
        continue
    try:
        evt = json.loads(line)
    except Exception:
        continue
    if evt.get('type') == 'result':
        result = evt.get('result', '')
        m = re.search(r'<optimization_status>(.*?)</optimization_status>', result)
        print(m.group(1) if m else '')
        break
" "$ROUND_FILE" 2>/dev/null || true)

    # Fallback: grep the raw file if python extraction failed
    if [ -z "$STATUS_VALUE" ]; then
        STATUS_VALUE=$(grep -oP '<optimization_status>\K[^<]+' "$ROUND_FILE" 2>/dev/null | tail -1 || true)
    fi

    # Log progress
    echo "$(date -Iseconds) round=$round status=\"${STATUS_VALUE:-no tag}\"" >> "$PROGRESS_LOG"
    log_info "Status: ${STATUS_VALUE:-no tag found}"

    if [ "$STATUS_VALUE" = "requirements met" ]; then
        echo ""
        log_info "Optimization complete! Requirements met after $round round(s)."
        log_info "Log dir: $LOG_DIR"
        log_info "Progress: $PROGRESS_LOG"
        EXPERIMENT_END=$(date -Iseconds)
        EXPERIMENT_END_EPOCH=$(date +%s)
        EXPERIMENT_DURATION=$((EXPERIMENT_END_EPOCH - EXPERIMENT_START_EPOCH))
        python3 "$SCRIPT_DIR/assemble-manifest.py" \
            --tenant "$TENANT_ID" \
            --log-dir "$LOG_DIR" \
            --task-model "$TASK_MODEL" \
            --started-at "$EXPERIMENT_START" \
            --completed-at "$EXPERIMENT_END" \
            --duration "$EXPERIMENT_DURATION" \
            --status "success" \
            --rounds "$round" || log_warn "Manifest assembly failed (non-fatal)"
        exit 0
    fi

    # "requirements not met" or missing tag → continue
    if [ "$round" -lt "$MAX_ROUNDS" ]; then
        log_info "Continuing to next round..."
    fi
done

echo ""
log_warn "Reached max rounds ($MAX_ROUNDS) without meeting requirements."
log_info "Log dir: $LOG_DIR"
log_info "Progress: $PROGRESS_LOG"
EXPERIMENT_END=$(date -Iseconds)
EXPERIMENT_END_EPOCH=$(date +%s)
EXPERIMENT_DURATION=$((EXPERIMENT_END_EPOCH - EXPERIMENT_START_EPOCH))
python3 "$SCRIPT_DIR/assemble-manifest.py" \
    --tenant "$TENANT_ID" \
    --log-dir "$LOG_DIR" \
    --task-model "$TASK_MODEL" \
    --started-at "$EXPERIMENT_START" \
    --completed-at "$EXPERIMENT_END" \
    --duration "$EXPERIMENT_DURATION" \
    --status "max_rounds" \
    --rounds "$MAX_ROUNDS" || log_warn "Manifest assembly failed (non-fatal)"
exit 1
