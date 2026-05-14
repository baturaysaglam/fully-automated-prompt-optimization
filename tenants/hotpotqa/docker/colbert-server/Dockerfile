# Runtime image for ColBERT server.
# Data can be baked in via COPY data/ or mounted at runtime via DATA_DIR env var.
FROM python:3.11-slim

# libgomp1: FAISS OpenMP support
# git: colbert-ai transitive dep (GitPython)
# g++ ninja-build: ColBERT JIT-compiles segmented_maxsim_cpp on first load
RUN apt-get update && apt-get install -y --no-install-recommends \
        git libgomp1 g++ ninja-build && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY start_colbert_server.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8893

ENTRYPOINT ["./entrypoint.sh"]
