#!/usr/bin/env bash
# =============================================================================
# Run Hephaestus Evals on Kubernetes
# =============================================================================
# Orchestrates evaluation runs on a Kubernetes cluster:
#   1. Ensures eval pod is running
#   2. Syncs code + tenant data to pod
#   3. Installs deps (first run)
#   4. Runs the eval with config
#
# Usage:
#   ./run_eval.sh --config <config.json>           # Run eval interactively
#   ./run_eval.sh --config <config.json> --detach   # Run in background
#   ./run_eval.sh --collect <run-name>              # Collect results locally
#   ./run_eval.sh --status <run-name>               # Check progress
#   ./run_eval.sh --logs <run-name>                 # Tail logs from detached run
#   ./run_eval.sh --stop <run-name>                 # Stop detached run
#   ./run_eval.sh --cleanup [--age <duration>]      # Clean up stale eval pods
#
# Each run creates a dedicated pod: hephaestus-<tenant_id>-<hash>
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/common.sh"

# Pod config
RESULTS_BASE="$MOUNT_PATH/heph-results"
EXEC_CONTAINER=""

# Extract tenant_id from a run name (format: hephaestus-<tenant_id>-<hash>).
tenant_from_run_name() {
    local run_name="$1"
    # Strip the hephaestus- prefix, then remove the last -<segment> (the hash)
    local stripped="${run_name#hephaestus-}"
    echo "${stripped%-*}"
}

# Set EXEC_CONTAINER when a tenant pod template exists (multi-container pod).
# The eval-runner container may not be the first container, so we must target it.
set_exec_container() {
    local tenant_id="$1"
    local tenant_template="$PROJECT_ROOT/tenants/$tenant_id/deploy/pod-template.yaml"
    if [ -f "$tenant_template" ]; then
        EXEC_CONTAINER="-c eval-runner"
    else
        EXEC_CONTAINER=""
    fi
}

# Load run metadata (.run_meta) from PVC to discover the pod name for a run.
# Sets POD_NAME for the caller.
load_run_meta() {
    local run_name="$1"
    local meta_path="$RESULTS_BASE/${run_name}/.run_meta"

    # Try to read .run_meta from the run's own pod first (if still alive)
    local pod_status
    pod_status=$(kctl get pod "$run_name" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
    if [ "$pod_status" == "Running" ]; then
        POD_NAME="$run_name"
        return 0
    fi

    # Otherwise, find any running hephaestus pod to read the PVC
    local reader_pod
    reader_pod=$(kctl get pods -l app=hephaestus -o name 2>/dev/null | head -1 | sed 's|^pod/||')
    if [ -z "$reader_pod" ]; then
        log_error "No running hephaestus pods found to read run metadata."
        log_info "The run's pod ($run_name) is no longer running."
        log_info "Launch any eval pod first, then retry."
        exit 1
    fi

    local meta_content
    meta_content=$(kctl exec "$reader_pod" -- cat "$meta_path" 2>/dev/null || true)
    if [ -z "$meta_content" ]; then
        log_error "No .run_meta found for run: $run_name"
        exit 1
    fi

    POD_NAME=$(echo "$meta_content" | python3 -c "import json,sys; print(json.load(sys.stdin)['pod'])")
}

# =============================================================================
# Help
# =============================================================================

show_help() {
    cat << 'EOF'
Hephaestus Kubernetes Eval Runner

USAGE:
    ./run_eval.sh --config <config.json> [--detach]
    ./run_eval.sh --collect <run-name>
    ./run_eval.sh --status <run-name>
    ./run_eval.sh --logs <run-name>
    ./run_eval.sh --stop <run-name>
    ./run_eval.sh --cleanup [--age <duration>]
    ./run_eval.sh --clean --tenant <tenant_id>

Each run creates a dedicated pod named hephaestus-<tenant_id>-<hash>.

OPTIONS:
    --config CONFIG     Path to eval config JSON (relative to project root)
    --detach            Run eval in background (survives disconnects)
    --collect RUN       Copy results from pod to ./local-results/<run-name>/
    --status RUN        Show eval progress for a run
    --logs RUN          Tail logs from a detached run
    --stop RUN          Stop a running detached eval
    --cleanup           Clean up stale eval pods
    --age DURATION      Max pod age for cleanup (default: 24h)
    --clean             Remove tenant's eval results from PVC (requires --tenant)
    --tenant TENANT     Tenant ID (used with --clean)
    -h, --help          Show this help

EXAMPLES:
    # Run an eval
    ./run_eval.sh --config tenants/<tenant_id>/configs/<config>.json

    # Run in background
    ./run_eval.sh --config tenants/<tenant_id>/configs/<config>.json --detach

    # Check progress
    ./run_eval.sh --status hephaestus-hotpotqa-m5kx7r

    # Collect results
    ./run_eval.sh --collect hephaestus-hotpotqa-m5kx7r

    # Clean up stale pods
    ./run_eval.sh --cleanup --age 24h

    # Remove tenant's eval results from PVC
    ./run_eval.sh --clean --tenant <tenant_id>

EOF
}

# =============================================================================
# Prereqs
# =============================================================================

ensure_pod() {
    local run_name="$1"
    local tenant_id="$2"
    log_step "Ensuring eval pod is running..."
    POD_NAME="$run_name" TENANT_ID="$tenant_id" "$SCRIPT_DIR/launch_eval_pod.sh"
}

# =============================================================================
# Code Sync
# =============================================================================

sync_code() {
    local tenant_id="$1"
    local remote_workspace="$2"

    log_step "Syncing code to pod..."
    log_info "  From: $PROJECT_ROOT"
    log_info "  To:   $POD_NAME:$remote_workspace"

    if [ ! -d "$PROJECT_ROOT/tenants/$tenant_id" ]; then
        log_error "Tenant directory not found: tenants/$tenant_id"
        exit 1
    fi

    # Build tar of all sync targets and extract on pod in one shot.
    # This replaces N separate kubectl cp calls with a single tar pipe.
    local tar_args=()
    for dir in src hephaestus; do
        [ -d "$PROJECT_ROOT/$dir" ] && tar_args+=("$dir")
    done
    [ -f "$PROJECT_ROOT/pyproject.toml" ] && tar_args+=("pyproject.toml")
    tar_args+=("tenants/$tenant_id")
    [ -f "$PROJECT_ROOT/.env" ] && tar_args+=(".env")

    if [ ${#tar_args[@]} -eq 0 ]; then
        log_error "Nothing to sync"
        exit 1
    fi

    log_info "  Syncing: ${tar_args[*]}"
    tar -chf - -C "$PROJECT_ROOT" "${tar_args[@]}" \
        | kctl exec -i $EXEC_CONTAINER "$POD_NAME" -- bash -c "mkdir -p '$remote_workspace' && tar -xf - -C '$remote_workspace'"

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warn "No .env file found at $PROJECT_ROOT/.env"
    fi

    log_info "Code sync complete"
}

# =============================================================================
# Dependencies
# =============================================================================

install_deps() {
    local tenant_id="$1"
    local remote_workspace="$2"
    local deps_marker="$remote_workspace/.deps_installed"

    # Install with tenant extras if defined in pyproject.toml (e.g. [hotpotqa]).
    local install_spec="$remote_workspace"
    if python3 -c "
import tomllib, sys
with open(sys.argv[1], 'rb') as f:
    extras = tomllib.load(f).get('project', {}).get('optional-dependencies', {})
sys.exit(0 if sys.argv[2] in extras else 1)
" "$PROJECT_ROOT/pyproject.toml" "$tenant_id" 2>/dev/null; then
        install_spec="${remote_workspace}[${tenant_id}]"
        log_info "Tenant extras detected: [$tenant_id]"
    fi

    # Hash pyproject.toml to detect dependency changes.
    # The marker stores the hash from the last install; if it differs, reinstall.
    local current_hash
    current_hash=$(md5sum "$PROJECT_ROOT/pyproject.toml" 2>/dev/null | cut -d' ' -f1 || echo "unknown")
    local stored_hash
    stored_hash=$(kctl exec $EXEC_CONTAINER "$POD_NAME" -- cat "$deps_marker" 2>/dev/null || true)

    if [ "$current_hash" = "$stored_hash" ]; then
        log_info "Dependencies up to date (skipping)"
        return 0
    fi

    log_step "Installing dependencies..."
    # Ensure git is available (needed for git+ pip dependencies)
    kctl exec $EXEC_CONTAINER "$POD_NAME" -- bash -c "command -v git >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq git >/dev/null 2>&1)"
    kctl exec $EXEC_CONTAINER "$POD_NAME" -- bash -c "pip install -q --upgrade pip && pip install -q -e '${install_spec}' && echo '$current_hash' > '$deps_marker'"
    log_info "Dependencies installed"
}

# =============================================================================
# Config Rewriting
# =============================================================================

rewrite_config() {
    local config_path="$1"
    local run_name="$2"
    local remote_workspace="$3"
    local remote_output_dir="$RESULTS_BASE/$run_name"

    # Rewrite output_dir and inject run_id, pipe directly to pod (no temp file)
    local patched_config
    patched_config=$(python3 -c "
import json, sys
config = json.load(open(sys.argv[1]))
config['output_dir'] = sys.argv[2]
config['run_id'] = sys.argv[3]
print(json.dumps(config, indent=2))
" "$PROJECT_ROOT/$config_path" "$remote_output_dir" "$run_name")

    local remote_config="$remote_workspace/patched-config-${run_name}.json"
    echo "$patched_config" | kctl exec -i $EXEC_CONTAINER "$POD_NAME" -- bash -c \
        "mkdir -p '$remote_output_dir' && cat > '$remote_config'"

    log_info "Config patched: output_dir → $remote_output_dir"
    # Return the remote config path for the caller
    PATCHED_CONFIG_PATH="$remote_config"
}

# =============================================================================
# Run
# =============================================================================

run_eval() {
    local config_path="$1"
    local detach="$2"

    # Parse tenant_id from config
    local tenant_id
    tenant_id=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['tenant_id'])" "$PROJECT_ROOT/$config_path")
    validate_tenant_id "$tenant_id"
    set_exec_container "$tenant_id"

    # Generate unified run name via Python run_id module
    local run_name
    run_name=$(python3 -c "from src.hephaestus.runs.run_id import generate_run_id; print(generate_run_id('$tenant_id'))")

    # Per-run workspace and pod
    local remote_workspace="/tmp/${run_name}"
    POD_NAME="$run_name"

    echo ""
    echo "========================================"
    echo "  Hephaestus Eval Runner (K8s)"
    echo "========================================"
    echo "  Config:    $config_path"
    echo "  Tenant:    $tenant_id"
    echo "  Run name:  $run_name"
    echo "  Pod:       $POD_NAME"
    echo "  Mode:      $([ "$detach" == "true" ] && echo "DETACHED (background)" || echo "interactive")"
    echo "  Results:   $RESULTS_BASE/$run_name/"
    echo "========================================"

    ensure_pod "$run_name" "$tenant_id"

    sync_code "$tenant_id" "$remote_workspace"
    install_deps "$tenant_id" "$remote_workspace"
    rewrite_config "$config_path" "$run_name" "$remote_workspace"

    local eval_cmd="cd $remote_workspace"
    eval_cmd+=" && set -a && source .env 2>/dev/null; set +a"
    eval_cmd+=" && export PYTHONUNBUFFERED=1"
    eval_cmd+=' && python -m hephaestus.cli eval --config "$1"'

    log_step "Running eval..."
    log_info "Config (remote): $PATCHED_CONFIG_PATH"
    echo ""

    if [ "$detach" == "true" ]; then

        local log_file="$RESULTS_BASE/$run_name/eval.log"
        local pid_file="$RESULTS_BASE/$run_name/.pid"
        local meta_file="$RESULTS_BASE/$run_name/.run_meta"

        # Write a helper script to the pod to avoid deeply nested quoting.
        # The helper runs the eval in the background via nohup, records the PID,
        # and auto-cleans up the pod on completion.
        cat <<HELPER_EOF | kctl exec -i $EXEC_CONTAINER "$POD_NAME" -- bash -c "cat > '$remote_workspace/run-detached.sh' && chmod +x '$remote_workspace/run-detached.sh'"
#!/usr/bin/env bash
set -u
CONFIG="\$1"
LOG_FILE="\$2"
PID_FILE="\$3"
RUN_NAME="\$4"
RESULTS_BASE="\$5"
NAMESPACE="\$6"

nohup bash -c '
cd $remote_workspace
set -a; source .env 2>/dev/null; set +a
export PYTHONUNBUFFERED=1
python -m hephaestus.cli eval --config "\$1"
exit_code=\$?
echo "{\"status\": \"completed\", \"exit_code\": \$exit_code}" > "\$3/\$2/.completed"
rm -f "\$3/\$2/.pid"
echo \$exit_code > /tmp/.heph-exit-code
# Kill sleep infinity so the container exits and pod transitions to Succeeded phase
pkill -f "sleep infinity" 2>/dev/null || true
' _ "\$CONFIG" "\$RUN_NAME" "\$RESULTS_BASE" "\$NAMESPACE" > "\$LOG_FILE" 2>&1 &

echo \$! > "\$PID_FILE"
echo \$! > /tmp/.heph-pid.tmp && mv /tmp/.heph-pid.tmp /tmp/.heph-pid
HELPER_EOF

        kctl exec $EXEC_CONTAINER "$POD_NAME" -- bash "$remote_workspace/run-detached.sh" \
            "$PATCHED_CONFIG_PATH" "$log_file" "$pid_file" "$run_name" "$RESULTS_BASE" "$NAMESPACE"

        # Write run metadata so --logs/--stop/--collect can discover the pod
        local pid_val
        pid_val=$(kctl exec $EXEC_CONTAINER "$POD_NAME" -- cat "$pid_file" 2>/dev/null || true)
        echo "{\"pod\": \"$POD_NAME\", \"pid\": \"$pid_val\"}" \
            | kctl exec -i $EXEC_CONTAINER "$POD_NAME" -- bash -c "cat > '$meta_file'"

        # Wait for the background process to start (up to 10s)
        local new_pid=""
        for _ in 1 2 3 4 5; do
            sleep 2
            new_pid=$(kctl exec $EXEC_CONTAINER "$POD_NAME" -- bash -c \
                "pid=\$(cat '$pid_file' 2>/dev/null) && [ -d /proc/\$pid ] && echo \$pid" 2>/dev/null || true)
            if [ -n "$new_pid" ]; then
                break
            fi
            # Check if PID file exists but process already exited (immediate crash)
            local stale_pid
            stale_pid=$(kctl exec $EXEC_CONTAINER "$POD_NAME" -- cat "$pid_file" 2>/dev/null || true)
            if [ -n "$stale_pid" ] && ! kctl exec $EXEC_CONTAINER "$POD_NAME" -- test -d "/proc/$stale_pid" 2>/dev/null; then
                log_error "Eval process started (PID: $stale_pid) but exited immediately."
                log_error "Last 30 lines of log:"
                kctl exec $EXEC_CONTAINER "$POD_NAME" -- tail -30 "$log_file" 2>/dev/null || true
                kctl exec $EXEC_CONTAINER "$POD_NAME" -- rm -f "$pid_file"
                exit 1
            fi
        done
        if [ -n "$new_pid" ]; then
            echo ""
            log_info "Eval started in background!"
            log_info "  PID:     $new_pid"
            echo -e "${GREEN}[INFO]${NC}   Results: ${BOLD}${CYAN}$RESULTS_BASE/$run_name/${NC}"
            echo -e "${GREEN}[INFO]${NC}   Log:     ${BOLD}${CYAN}$log_file${NC}"
            echo ""
            log_info "Commands:"
            log_info "  View logs:    ./run_eval.sh --logs $run_name"
            log_info "  Check status: ./run_eval.sh --status $run_name"
            log_info "  Stop:         ./run_eval.sh --stop $run_name"
            log_info "  Collect:      ./run_eval.sh --collect $run_name"
            echo ""
            log_info "Pod will auto-delete on eval completion."
        else
            log_error "Failed to start eval"
            kctl exec $EXEC_CONTAINER "$POD_NAME" -- cat "$log_file" 2>/dev/null | tail -20
            exit 1
        fi
    else
        local exec_flags=(-i); [ -t 0 ] && exec_flags+=(-t)
        kctl exec "${exec_flags[@]}" $EXEC_CONTAINER "$POD_NAME" -- bash -c "$eval_cmd" _ "$PATCHED_CONFIG_PATH"
        echo ""
        log_info "Eval complete. Run name: $run_name"
        log_info "Collect results: ./run_eval.sh --collect $run_name"
        echo ""
        log_info "To delete the pod when done inspecting:"
        log_info "  kubectl -n \$NAMESPACE delete pod $POD_NAME"
    fi
}

# =============================================================================
# Collect
# =============================================================================

collect_results() {
    local run_name="$1"
    validate_run_name "$run_name"
    load_run_meta "$run_name"
    local local_dir="$PROJECT_ROOT/local-results/$run_name"

    log_step "Collecting results for: $run_name"

    # Verify the pod is running before attempting to collect
    local status
    status=$(kctl get pod "$POD_NAME" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
    if [ "$status" != "Running" ]; then
        # Try any hephaestus pod as a reader since results are on the PVC
        local reader_pod
        reader_pod=$(kctl get pods -l app=hephaestus -o name 2>/dev/null | head -1 | sed 's|^pod/||')
        if [ -z "$reader_pod" ]; then
            log_error "No running hephaestus pods found. Cannot collect results."
            log_info "Results live on the PVC and survive pod restarts. Launch any eval pod first."
            exit 1
        fi
        log_info "Run's pod is gone; using $reader_pod to read PVC results."
        POD_NAME="$reader_pod"
    fi

    # Verify the results directory exists on the pod
    if ! kctl exec "$POD_NAME" -- test -d "$RESULTS_BASE/$run_name" 2>/dev/null; then
        log_error "Results directory not found on pod: $RESULTS_BASE/$run_name"
        log_info "Available runs:"
        kctl exec "$POD_NAME" -- ls "$RESULTS_BASE" 2>/dev/null || log_warn "No results directory found"
        exit 1
    fi

    mkdir -p "$local_dir"
    kctl exec "$POD_NAME" -- tar -cf - -C "$RESULTS_BASE/$run_name" . \
        | tar -xf - -C "$local_dir"

    echo -e "${GREEN}[INFO]${NC} Results saved to: ${BOLD}${CYAN}$local_dir${NC}"
    ls -la "$local_dir"
}

# =============================================================================
# Status
# =============================================================================

show_status() {
    local run_name="$1"
    validate_run_name "$run_name"
    load_run_meta "$run_name"

    log_step "Checking eval progress: $run_name"

    kctl exec "$POD_NAME" -- cat "$RESULTS_BASE/$run_name/progress.json" 2>/dev/null || {
        log_warn "No progress.json found for run: $run_name"
        return 1
    }
}

# =============================================================================
# Logs
# =============================================================================

show_logs() {
    local run_name="$1"
    validate_run_name "$run_name"
    load_run_meta "$run_name"

    local log_file="$RESULTS_BASE/$run_name/eval.log"

    log_step "Tailing logs from detached run..."
    echo -e "${GREEN}[INFO]${NC} Log file: ${BOLD}${CYAN}$log_file${NC}"
    log_info "Press Ctrl+C to stop tailing (eval continues running)"
    echo ""
    kctl exec "$POD_NAME" -- tail -f "$log_file" 2>/dev/null || {
        log_error "No logs found. Is an eval running?"
    }
}

# =============================================================================
# Stop
# =============================================================================

stop_eval() {
    local run_name="$1"
    validate_run_name "$run_name"
    load_run_meta "$run_name"

    local pid_file="$RESULTS_BASE/$run_name/.pid"

    log_step "Stopping eval..."

    local pid
    pid=$(kctl exec "$POD_NAME" -- cat "$pid_file" 2>/dev/null || true)
    if [ -n "$pid" ]; then
        if ! [[ "$pid" =~ ^[0-9]+$ ]]; then
            log_error "Invalid PID in pid file: $pid"
            exit 1
        fi
        # Use /proc to get the process group (portable, no procps needed), fall back to kill by PID.
        # Clean up PID file in the same exec to avoid an extra round-trip.
        # Pass pid and PID file path as positional args to avoid interpolation.
        kctl exec "$POD_NAME" -- bash -c \
            '[ -f /tmp/.heph-exit-code ] || echo 1 > /tmp/.heph-exit-code; pgid=$(cut -d" " -f5 /proc/"$1"/stat 2>/dev/null) && kill -- -"$pgid" 2>/dev/null || kill "$1" 2>/dev/null; rm -f "$2"' \
            _ "$pid" "$pid_file" && {
            log_info "Eval stopped (PID: $pid)"
        } || {
            log_warn "Process not running or already stopped"
        }
    else
        log_info "No eval running"
    fi
}

# =============================================================================
# Cleanup
# =============================================================================

cleanup_pods() {
    local max_age="${1:-24h}"

    log_step "Cleaning up stale eval pods..."

    # Convert max_age to seconds
    local max_age_secs
    if [[ "$max_age" =~ ^([0-9]+)h$ ]]; then
        max_age_secs=$(( ${BASH_REMATCH[1]} * 3600 ))
    elif [[ "$max_age" =~ ^([0-9]+)m$ ]]; then
        max_age_secs=$(( ${BASH_REMATCH[1]} * 60 ))
    elif [[ "$max_age" =~ ^([0-9]+)d$ ]]; then
        max_age_secs=$(( ${BASH_REMATCH[1]} * 86400 ))
    else
        log_error "Invalid age format: $max_age (use e.g. 24h, 30m, 2d)"
        exit 1
    fi

    # List all hephaestus eval pods
    local pods_json
    pods_json=$(kctl get pods -l "app=hephaestus,component=evaluation" -o json 2>/dev/null)
    local pod_count
    pod_count=$(echo "$pods_json" | python3 -c "import json,sys; print(len(json.load(sys.stdin).get('items',[])))")

    if [ "$pod_count" -eq 0 ]; then
        log_info "No eval pods found."
        return 0
    fi

    log_info "Found $pod_count eval pod(s):"
    echo ""

    local deleted=0
    local skipped=0

    # Classify each pod
    echo "$pods_json" | python3 -c "
import json, sys, datetime

data = json.load(sys.stdin)
now = datetime.datetime.now(datetime.timezone.utc)
max_age = int(sys.argv[1])

for pod in data.get('items', []):
    name = pod['metadata']['name']
    phase = pod['status'].get('phase', 'Unknown')
    created = datetime.datetime.fromisoformat(pod['metadata']['creationTimestamp'].replace('Z', '+00:00'))
    age_secs = (now - created).total_seconds()
    age_str = f'{int(age_secs/3600)}h{int((age_secs%3600)/60)}m'
    run_name = pod['metadata'].get('labels', {}).get('hephaestus/run-name', name)

    if phase in ('Succeeded', 'Failed'):
        status = 'COMPLETED'
    elif age_secs > max_age:
        status = 'STALE'
    else:
        status = 'ACTIVE'

    print(f'{status}\t{name}\t{phase}\t{age_str}\t{run_name}')
" "$max_age_secs" | while IFS=$'\t' read -r classification pod_name phase age run_name; do
        case "$classification" in
            COMPLETED)
                echo -e "  ${GREEN}[DELETE]${NC} $pod_name (phase=$phase, age=$age)"
                kctl delete pod "$pod_name" --wait=false 2>/dev/null || true
                deleted=$((deleted + 1))
                ;;
            STALE)
                echo -e "  ${YELLOW}[STALE]${NC}  $pod_name (phase=$phase, age=$age)"
                # Check if eval is still running
                local pid
                pid=$(kctl exec "$pod_name" -- cat "$RESULTS_BASE/$run_name/.pid" 2>/dev/null || true)
                if [ -n "$pid" ] && kctl exec "$pod_name" -- test -d "/proc/$pid" 2>/dev/null; then
                    echo -e "           ${YELLOW}Still running (PID: $pid). Skipping.${NC}"
                    skipped=$((skipped + 1))
                else
                    echo -e "           ${YELLOW}No active eval. Delete with:${NC}"
                    echo "           kubectl -n \$NAMESPACE delete pod $pod_name"
                    skipped=$((skipped + 1))
                fi
                ;;
            ACTIVE)
                echo -e "  ${BLUE}[ACTIVE]${NC} $pod_name (phase=$phase, age=$age) — skipping"
                skipped=$((skipped + 1))
                ;;
        esac
    done

    echo ""
    log_info "Cleanup complete."
}

# =============================================================================
# Clean
# =============================================================================

clean_results() {
    local tenant_id="$1"
    validate_tenant_id "$tenant_id"
    set_pod_name "$tenant_id"

    log_step "Cleaning eval results for tenant: $tenant_id"

    # Verify pod is running
    local status
    status=$(kctl get pod "$POD_NAME" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
    if [ "$status" != "Running" ]; then
        log_error "Pod '$POD_NAME' is not running (status: $status). Cannot clean results."
        log_info "Re-launch the pod first: bash deploy/scripts/launch_eval_pod.sh"
        exit 1
    fi

    # Safety check: refuse if a detached eval is running for this tenant
    local existing_pid
    existing_pid=$(kctl exec "$POD_NAME" -- cat "$REMOTE_PID" 2>/dev/null || true)
    if [ -n "$existing_pid" ] && kctl exec "$POD_NAME" -- test -d "/proc/$existing_pid" 2>/dev/null; then
        log_error "A detached eval is running for tenant '$tenant_id' (PID: $existing_pid)"
        log_info "Stop it first: ./run_eval.sh --stop <run-name>"
        exit 1
    fi

    # List matching run dirs
    local matching_dirs
    matching_dirs=$(kctl exec "$POD_NAME" -- bash -c "ls '$RESULTS_BASE' 2>/dev/null | grep '^${tenant_id}-'" || true)

    if [ -z "$matching_dirs" ]; then
        log_info "No eval results found for tenant '$tenant_id'"
        return 0
    fi

    local count
    count=$(echo "$matching_dirs" | wc -l)

    log_info "Found $count run(s) for tenant '$tenant_id':"
    echo "$matching_dirs" | sed 's/^/    /'
    echo ""

    read -p "Delete $count run(s) for tenant '$tenant_id'? [yes/N]: " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Aborted"
        return 0
    fi

    # Delete tenant run dirs and metadata
    kctl exec "$POD_NAME" -- bash -c "rm -rf $RESULTS_BASE/${tenant_id}-*/"
    kctl exec "$POD_NAME" -- bash -c "rm -f '$REMOTE_PID' '$REMOTE_LOG_LINK'"

    log_info "Deleted $count run(s) and metadata for tenant '$tenant_id'"
}

# =============================================================================
# Main
# =============================================================================

main() {
    local action="run"
    local config=""
    local detach="false"
    local run_name=""
    local cleanup_age="24h"
    local tenant_id=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                config="$2"
                shift 2
                ;;
            --detach)
                detach="true"
                shift
                ;;
            --collect)
                action="collect"
                if [[ $# -lt 2 ]]; then
                    log_error "--collect requires a run name"
                    exit 1
                fi
                run_name="$2"
                shift 2
                ;;
            --status)
                action="status"
                if [[ $# -lt 2 ]]; then
                    log_error "--status requires a run name"
                    exit 1
                fi
                run_name="$2"
                shift 2
                ;;
            --logs)
                action="logs"
                if [[ $# -lt 2 ]]; then
                    log_error "--logs requires a run name"
                    exit 1
                fi
                run_name="$2"
                shift 2
                ;;
            --stop)
                action="stop"
                if [[ $# -lt 2 ]]; then
                    log_error "--stop requires a run name"
                    exit 1
                fi
                run_name="$2"
                shift 2
                ;;
            --cleanup)
                action="cleanup"
                shift
                ;;
            --age)
                cleanup_age="$2"
                shift 2
                ;;
            --clean)
                action="clean"
                shift
                ;;
            --tenant)
                if [[ $# -lt 2 ]]; then
                    log_error "--tenant requires a tenant ID"
                    exit 1
                fi
                tenant_id="$2"
                shift 2
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

    check_kubectl

    case "$action" in
        run)
            if [ -z "$config" ]; then
                log_error "--config is required for run mode"
                show_help
                exit 1
            fi
            if [ ! -f "$PROJECT_ROOT/$config" ]; then
                log_error "Config file not found: $PROJECT_ROOT/$config"
                exit 1
            fi
            run_eval "$config" "$detach"
            ;;
        collect)
            collect_results "$run_name"
            ;;
        status)
            show_status "$run_name"
            ;;
        logs)
            show_logs "$run_name"
            ;;
        stop)
            stop_eval "$run_name"
            ;;
        cleanup)
            cleanup_pods "$cleanup_age"
            ;;
        clean)
            if [ -z "$tenant_id" ]; then
                log_error "--clean requires --tenant <tenant_id>"
                exit 1
            fi
            clean_results "$tenant_id"
            ;;
        *)
            log_error "Unknown action: $action"
            exit 1
            ;;
    esac
}

main "$@"
