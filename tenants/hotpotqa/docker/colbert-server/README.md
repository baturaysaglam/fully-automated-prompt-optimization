<!--
Copyright 2026 Cisco Systems, Inc. and its affiliates

SPDX-License-Identifier: Apache-2.0
-->

# ColBERT-K Wikipedia Retrieval Server (Docker) — DEPRECATED

> **Note:** ColBERT retrieval has been replaced by in-process BM25 (`bm25s`).
> See `tenants/hotpotqa/code/retrieval.py` for the new implementation.
> This Docker image is kept for reference only.

---

Docker image for the ColBERTv2 wiki17_abstracts retrieval server used by GEPA's HotpotQA multi-hop chain.

## Two-Phase Build Workflow

The index build is offloaded to a GPU via SkyPilot (~10-15 min on H100), then the Docker image
simply copies the pre-built index from the build context. No indexing happens during `docker build`.

### Phase 1: Build the index on GPU

```bash
cd tenants/hotpotqa/docker/colbert-server

export SKYPILOT_API_SERVER_ENDPOINT=http://skypilot.rbst.io:8080
sky jobs launch --name colbert-index-build skypilot-build-index.yaml -y

# Monitor progress
sky jobs queue
sky jobs logs <job-id>
```

The YAML embeds all kubernetes config (kueue queue `skypilot-jobs-1-gpu`, PVC mount
`csi-pvc-mounted` at `/shared-storage`, etc.) so no separate config file is needed.

The job downloads the raw HotpotQA abstracts, builds `collection.tsv`, and runs the ColBERT
indexer on GPU. Results are written to `/shared-storage/hotpotqa/colbert-data/` on the PVC.

### Phase 2: Build and push the Docker image

The image does **not** bake in data — it mounts the PVC at runtime.

```bash
cd tenants/hotpotqa/docker/colbert-server

# Build (fast — just code + deps, <2 min)
docker build -t colbert-wiki17:0.3 .

# Push to your container registry
REGISTRY=your-registry
docker tag colbert-wiki17:0.3 $REGISTRY/colbert-wiki17:0.3
docker push $REGISTRY/colbert-wiki17:0.3
```

### Phase 3: Deploy to Kubernetes

The deployment runs a 3-replica fleet behind a single ClusterIP Service.
K8s round-robins queries across healthy pods for ~3x throughput.

```bash
kubectl apply -f k8s-deploy.yaml

# Watch until all 3 pods reach READY 1/1 (~2 min for index load)
kubectl get pods -l app=colbert-server -n your-namespace -w

# Verify all 3 endpoints are registered
kubectl get endpoints colbert-server -n your-namespace
```

The deployment mounts the `csi-pvc-mounted` PVC and points `DATA_DIR` and
`CHECKPOINT_DIR` to the pre-built data on the PVC. No local data download needed.

**Resource footprint:** 3 pods × (4 CPU req / 16Gi RAM) = 12 CPU / 48Gi RAM total requests.
A `PodDisruptionBudget` (`minAvailable: 1`) prevents node drains from evicting all pods at once.

## Data Sources

| Artifact | URL | Size |
|----------|-----|------|
| Raw abstracts | `nlp.stanford.edu/projects/hotpotqa/enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2` | ~1.5 GB |
| ColBERTv2 checkpoint | `downloads.cs.stanford.edu/nlp/data/colbert/colbertv2/colbertv2.0.tar.gz` | ~150 MB |

> **Note:** The previously hosted pre-built index and collection.tsv at
> `downloads.cs.stanford.edu` are no longer available (404). The SkyPilot job rebuilds
> them from the raw abstracts instead.

## Querying the Server

The server exposes a single `GET /` endpoint:

```
GET /?query=<search text>&k=<num results>
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `query`   | yes      | —       | Search text (URL-encoded) |
| `k`       | no       | `3`     | Number of passages to return |

**Response** (JSON):

```json
{
  "query": "capital of France",
  "k": 3,
  "passages": [
    "Paris. Paris (] ) is the capital and most populous city of France...",
    "Administration of Paris. As the capital of France, Paris is the seat of...",
    "Capital (French magazine). Capital is a monthly French economics..."
  ],
  "scores": [26.85, 26.13, 25.49]
}
```

**Examples:**

```bash
# From within the cluster (via ClusterIP service)
curl "http://colbert-server:8893/?query=capital+of+France&k=3"

# Via port-forward for local access
kubectl port-forward svc/colbert-server 8893:8893
curl "http://localhost:8893/?query=capital+of+France&k=3"

# Multi-hop style query
curl "http://colbert-server:8893/?query=Who+directed+the+film+starring+the+actress+born+in+1990&k=5"
```

**Error responses** return JSON with an `error` field:

| Status | Condition |
|--------|-----------|
| `400`  | Missing `query` parameter, or `k` is not a positive integer |
| `500`  | Search failed (internal ColBERT error) |

## Environment Variables

| Variable         | Default     | Description                                    |
|------------------|-------------|------------------------------------------------|
| `DATA_DIR`       | `/app/data` | Path to directory with `index/` + `collection.tsv` |
| `CHECKPOINT_DIR` | (from index metadata) | Path to ColBERTv2 checkpoint directory (overrides index metadata) |
| `PORT`           | `8893`      | TCP port the server listens on                 |

## Memory Requirements

The server loads the full wiki17_abstracts index into memory. Expect **4-6 GB RAM** usage.
Index load takes ~2 minutes on first startup (includes JIT-compiling C++ extensions).

## Why faiss-gpu is built from source

The pip `faiss-gpu-cu12` wheel has three compatibility problems with the NGC
`pytorch:23.10-py3` image on H100 GPUs:

1. **Missing sm_90 kernels**: the pip wheel is compiled for older CUDA architectures
   (sm_70–sm_86) and does not include sm_90 (H100), causing
   `CUDA error 209: no kernel image is available for execution on the device` during
   k-means clustering.
2. **cublas version mismatch**: faiss's `loader.py` preloads cublas via the pip
   `nvidia-cublas-cu12` package, which ships a `libcublas.so.12` that is mismatched
   with the container's CUDA driver (`undefined symbol: cublasLtGetEnvironmentMode`).
   The env var `_FAISS_WHEEL_DISABLE_CUDA_PRELOAD=1` bypasses this for the pip wheel,
   but building from source avoids the issue entirely.
3. **numpy 2.x dependency**: recent pip wheels are built against NumPy 2.x
   (`numpy._core`), but NGC torch requires NumPy 1.x, causing `ModuleNotFoundError`
   on import.

The fix is to build faiss v1.9.0 from source with `-DCMAKE_CUDA_ARCHITECTURES=90`,
which produces a faiss-gpu linked against the NGC image's system CUDA. The built
package is cached on the PVC so subsequent jobs skip the build step.

## CPU-Only Fallback

For environments without SkyPilot/GPU access, use the standalone 3-stage Dockerfile that
builds the index on CPU during `docker build`:

```bash
docker build -f Dockerfile.cpu-standalone -t colbert-wiki17:0.1 .
```

This takes 4+ hours and requires 8+ GB RAM.

## Usage with HotpotQA Eval

The baseline eval script defaults to ColBERT as the retrieval backend. Three
modes are available via `--retrieval-backend`:

| Mode | Description |
|------|-------------|
| `colbert` (default) | Starts a **local** ColBERT server (requires local index data) |
| `wikipedia` | Starts a local Wikipedia API proxy (no index needed) |
| `remote` | Connects to the **k8s-deployed** ColBERT service — no local server started |

### Running with the deployed ColBERT service

From a pod with cluster network access:

```bash
# Val split (default)
python tenants/hotpotqa/scripts/run_baseline_eval.py --retrieval-backend remote --split val

# Train split (for prompt optimization)
python tenants/hotpotqa/scripts/run_baseline_eval.py --retrieval-backend remote --split train

# Test split (for final evaluation)
python tenants/hotpotqa/scripts/run_baseline_eval.py --retrieval-backend remote --split test
```

The script selects the split-specific remote config automatically:
- `val` → `configs/remote-chain-variant001.json`
- `train` → `configs/remote-chain-variant001-train.json`
- `test` → `configs/remote-chain-variant001-test.json`

Each config points `colbert_url` at `http://colbert-server:8893` (the ClusterIP
service) and writes results to a distinct output directory. The script
health-checks the remote server before starting the eval.

### Local access via port-forward

```bash
kubectl port-forward svc/colbert-server 8893:8893
python tenants/hotpotqa/scripts/run_baseline_eval.py --retrieval-backend colbert --split val
```

This uses `configs/local-chain-variant001.json` and starts a local ColBERT
server. For port-forward without local data, edit the config's `colbert_url`
to `http://localhost:8893` and use `--retrieval-backend remote`.
