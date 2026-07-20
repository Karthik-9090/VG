# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --user --cache-dir /root/.cache/pip --retries 20 --timeout 300 -r requirements.txt

# Production stage
FROM python:3.12-slim
WORKDIR /app
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /home/appuser/.local
COPY requirements.txt ./
COPY app_production.py ./
COPY security.py ./
COPY model_loader.py ./
COPY run_production.py ./
COPY models/production_lasso.pkl ./models/production_lasso.pkl

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app /home/appuser
USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "uvicorn", "app_production:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]
