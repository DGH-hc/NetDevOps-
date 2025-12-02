# ==========================
#   BUILDER IMAGE
# ==========================
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ==========================
#   RUNTIME IMAGE
# ==========================
FROM python:3.11-slim

WORKDIR /app

# copy dependencies installed in builder
COPY --from=builder /install /usr/local

# copy project code
COPY . /app

# ---- FIX: create logs directory as ROOT ----
RUN mkdir -p /app/logs && chmod -R 777 /app/logs

# Now create runtime user
RUN useradd -m appuser
USER appuser
# ---- FIX ENDS ----

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
