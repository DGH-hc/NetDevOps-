# ==========================
#   BUILDER
# ==========================
FROM python:3.11.6-slim AS builder

WORKDIR /build

RUN apt-get update \
 && apt-get install -y gcc \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==========================
#   RUNTIME
# ==========================
FROM python:3.11.6-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# non-root user
RUN useradd -m appuser

COPY --from=builder /install /usr/local
COPY . /app

RUN mkdir -p /app/logs \
 && chown -R appuser:appuser /app

USER appuser

# IMPORTANT:
# No CMD here.
# Runtime behavior is controlled by Kubernetes / Helm.
