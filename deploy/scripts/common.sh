#!/usr/bin/env bash
# =============================================================================
# Common utilities for Hephaestus deployment scripts
# =============================================================================

# Colors
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export CYAN='\033[0;36m'
export BOLD='\033[1m'
export NC='\033[0m'  # No Color

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step() { echo -e "\n${BLUE}==>${NC} $*"; }

# Mount path for the PVC inside containers
MOUNT_PATH="/shared-storage"

# Validation helpers (shared across scripts)
validate_dns_name() {
    local val="$1" label="$2"
    if [[ ! "$val" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]]; then
        log_error "$label must be a valid K8s name (lowercase alphanumeric, '-', '.'): $val"
        exit 1
    fi
}
validate_image_ref() {
    local val="$1" label="$2"
    if [[ ! "$val" =~ ^[a-zA-Z0-9._:/@-]+$ ]]; then
        log_error "$label contains invalid characters: $val"
        exit 1
    fi
}
validate_resource() {
    local val="$1" label="$2"
    if [[ ! "$val" =~ ^[0-9]+[A-Za-z]*$ ]]; then
        log_error "$label must be a valid K8s resource quantity (e.g., 2, 4Gi): $val"
        exit 1
    fi
}
validate_run_name() {
    local val="$1"
    if [[ ! "$val" =~ ^hephaestus-[a-z0-9_-]+-[a-z0-9]+$ ]]; then
        log_error "Invalid run name (expected hephaestus-<tenant_id>-<hash>): $val"
        exit 1
    fi
}
validate_tenant_id() {
    local val="$1"
    if [[ ! "$val" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        log_error "Invalid tenant_id (alphanumeric, '-', '_' only): $val"
        exit 1
    fi
}

# Require NAMESPACE to be set. Call explicitly in scripts that need it.
require_namespace() {
    if [ -z "${NAMESPACE:-}" ]; then
        log_error "NAMESPACE is required. Set it to your target K8s namespace, e.g.:"
        log_error "  export NAMESPACE=my-namespace"
        exit 1
    fi
}

# kubectl wrapper that injects --namespace
kctl() {
    kubectl --namespace "$NAMESPACE" "$@"
}

# Kubernetes check
check_kubectl() {
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl not found. Install kubectl and configure cluster access."
        exit 1
    fi
    require_namespace
    if ! kctl cluster-info &>/dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
        exit 1
    fi
}
