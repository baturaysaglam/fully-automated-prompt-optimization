#!/usr/bin/env bash
# =============================================================================
# Launch Hephaestus Evaluation Pod with PVC
# =============================================================================
# Creates a long-lived pod with PVC mounted for persistent results storage.
#
# USAGE:
#   ./launch_eval_pod.sh
#
# ENVIRONMENT VARIABLES:
#   POD_NAME    - Pod name (default: hephaestus-eval)
#   TENANT_ID   - Tenant ID for pod labeling (optional)
#   PVC_NAME    - PVC name (default: csi-pvc-mounted)
#   IMAGE       - Container image (default: python:3.11-slim)
#   CPU_REQ     - CPU request (default: 2)
#   CPU_LIM     - CPU limit (default: 4)
#   MEM_REQ     - Memory request (default: 4Gi)
#   MEM_LIM     - Memory limit (default: 8Gi)
# =============================================================================

set -euo pipefail

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/common.sh"

require_namespace
check_kubectl

POD_NAME="${POD_NAME:-hephaestus-eval}"
TENANT_ID="${TENANT_ID:-}"
PVC_NAME="${PVC_NAME:-csi-pvc-mounted}"
IMAGE="${IMAGE:-python:3.11-slim}"
CPU_REQ="${CPU_REQ:-2}"
CPU_LIM="${CPU_LIM:-4}"
MEM_REQ="${MEM_REQ:-4Gi}"
MEM_LIM="${MEM_LIM:-8Gi}"

# Validate inputs before interpolating into YAML
validate_dns_name "$POD_NAME" "POD_NAME"
validate_dns_name "$PVC_NAME" "PVC_NAME"
validate_image_ref "$IMAGE" "IMAGE"
validate_resource "$CPU_REQ" "CPU_REQ"
validate_resource "$CPU_LIM" "CPU_LIM"
validate_resource "$MEM_REQ" "MEM_REQ"
validate_resource "$MEM_LIM" "MEM_LIM"

echo "========================================"
echo "Launching Hephaestus Eval Pod"
echo "========================================"
echo "Pod name: $POD_NAME"
echo "PVC: $PVC_NAME"
echo "Image: $IMAGE"
echo "Resources: ${CPU_REQ}/${MEM_REQ} request, ${CPU_LIM}/${MEM_LIM} limit"
echo ""

# Check if pod already exists and is running
status=$(kctl get pod "$POD_NAME" -o jsonpath='{.status.phase}' 2>/dev/null || echo "NotFound")
if [ "$status" == "Running" ]; then
    log_info "Pod '$POD_NAME' is already running. Nothing to do."
    exit 0
elif [ "$status" != "NotFound" ]; then
    log_warn "Pod '$POD_NAME' exists but status is: $status. Deleting and recreating..."
    kctl delete pod "$POD_NAME" --wait=true
fi

# Build optional tenant label
TENANT_LABEL=""
if [ -n "$TENANT_ID" ]; then
    TENANT_LABEL="    hephaestus/tenant: ${TENANT_ID}"
fi

# Build optional run-name label (if POD_NAME follows hephaestus-<tenant>-<hash> pattern)
RUN_NAME_LABEL=""
if [[ "$POD_NAME" =~ ^hephaestus-[a-z0-9_-]+-[a-z0-9]+$ ]]; then
    RUN_NAME_LABEL="    hephaestus/run-name: ${POD_NAME}"
fi

# Check for a tenant-provided pod template
TENANT_TEMPLATE=""
if [ -n "$TENANT_ID" ]; then
    TENANT_TEMPLATE="$PROJECT_ROOT/tenants/$TENANT_ID/deploy/pod-template.yaml"
fi

if [ -n "$TENANT_TEMPLATE" ] && [ -f "$TENANT_TEMPLATE" ]; then
    log_info "Using tenant pod template: $TENANT_TEMPLATE"
    export POD_NAME NAMESPACE MOUNT_PATH
    envsubst '${POD_NAME} ${NAMESPACE} ${MOUNT_PATH}' < "$TENANT_TEMPLATE" | kctl apply -f -
else
    # Create pod with PVC (default inline template)
    log_info "Creating pod..."
    kctl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: ${POD_NAME}
  labels:
    app: hephaestus
    component: evaluation
${TENANT_LABEL:+$TENANT_LABEL}
${RUN_NAME_LABEL:+$RUN_NAME_LABEL}
spec:
  restartPolicy: Never
  containers:
  - name: python
    image: ${IMAGE}
    command: ["bash", "-c", "trap 'exit 0' TERM; while [ ! -f /tmp/.heph-pid ]; do sleep 2; done; tail --pid=\$(cat /tmp/.heph-pid) -f /dev/null; exit \$(cat /tmp/.heph-exit-code 2>/dev/null || echo 1)"]
    resources:
      requests:
        cpu: "${CPU_REQ}"
        memory: "${MEM_REQ}"
        ephemeral-storage: "5Gi"
      limits:
        cpu: "${CPU_LIM}"
        memory: "${MEM_LIM}"
        ephemeral-storage: "10Gi"
    volumeMounts:
    - name: workspace
      mountPath: ${MOUNT_PATH}
  volumes:
  - name: workspace
    persistentVolumeClaim:
      claimName: ${PVC_NAME}
EOF
fi

log_info "Waiting for pod to be ready..."
kctl wait --for=condition=Ready pod/"$POD_NAME" --timeout=1200s

echo ""
echo "========================================"
log_info "Pod '$POD_NAME' is ready!"
echo "========================================"
