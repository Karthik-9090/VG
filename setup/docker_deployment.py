"""
Docker deployment instructions and utilities for hourly AQI collection.

The collector service runs in a containerized environment with:
- Automatic hourly scheduling
- PostgreSQL connectivity
- Volume mounting for logs and backups
- Health monitoring
"""

import sys
from pathlib import Path

DOCKER_SERVICE_YAML = """
# Add this service to docker-compose.yml

  aqi-collector:
    build:
      context: .
      dockerfile: Dockerfile.collector
    container_name: vayuguard-aqi-collector
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: vayuguard
      DB_USER: vayuguard_user
      DB_PASSWORD: vayuguard_pass
      WAQI_API_KEY: ${WAQI_API_KEY}
    volumes:
      - ./data-pipeline/logs:/app/data-pipeline/logs
      - ./data-pipeline/backups:/app/data-pipeline/backups
    working_dir: /app
    command: python collector.py
"""

DOCKERFILE_COLLECTOR = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY data-pipeline/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \\
    pip install --no-cache-dir schedule

# Copy application files
COPY data-pipeline/ ./data-pipeline/
COPY collector.py .
COPY .env .

# Create log and backup directories
RUN mkdir -p data-pipeline/logs data-pipeline/backups

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=10s --retries=3 \\
    CMD python -c "import psycopg2; psycopg2.connect('host=postgres user=vayuguard_user password=vayuguard_pass dbname=vayuguard')" || exit 1

CMD ["python", "collector.py"]
"""

DOCKER_COMPOSE_STANDALONE = """
version: '3.9'

services:
  postgres:
    image: postgres:15
    container_name: vayuguard-postgres-collector
    restart: unless-stopped
    environment:
      POSTGRES_DB: vayuguard
      POSTGRES_USER: vayuguard_user
      POSTGRES_PASSWORD: vayuguard_pass
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    ports:
      - '5432:5432'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U vayuguard_user -d vayuguard"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  aqi-collector:
    build:
      context: .
      dockerfile: Dockerfile.collector
    container_name: vayuguard-aqi-collector
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: vayuguard
      DB_USER: vayuguard_user
      DB_PASSWORD: vayuguard_pass
      WAQI_API_KEY: ${WAQI_API_KEY}
    volumes:
      - ./data-pipeline/logs:/app/data-pipeline/logs
      - ./data-pipeline/backups:/app/data-pipeline/backups
    working_dir: /app
    command: python collector.py

volumes:
  pgdata:
"""

KUBE_DEPLOYMENT_YAML = """
# Kubernetes Deployment for AQI Collector (Optional)

apiVersion: apps/v1
kind: Deployment
metadata:
  name: vayuguard-aqi-collector
  namespace: vayuguard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: aqi-collector
  template:
    metadata:
      labels:
        app: aqi-collector
    spec:
      containers:
      - name: collector
        image: vayuguard-aqi-collector:latest
        imagePullPolicy: IfNotPresent
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: vayuguard-config
              key: db-host
        - name: DB_PORT
          valueFrom:
            configMapKeyRef:
              name: vayuguard-config
              key: db-port
        - name: DB_NAME
          valueFrom:
            configMapKeyRef:
              name: vayuguard-config
              key: db-name
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: vayuguard-secrets
              key: db-user
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: vayuguard-secrets
              key: db-password
        - name: WAQI_API_KEY
          valueFrom:
            secretKeyRef:
              name: vayuguard-secrets
              key: waqi-api-key
        volumeMounts:
        - name: logs
          mountPath: /app/data-pipeline/logs
        - name: backups
          mountPath: /app/data-pipeline/backups
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - |
              import psycopg2
              import os
              try:
                psycopg2.connect(
                  host=os.getenv('DB_HOST'),
                  port=int(os.getenv('DB_PORT')),
                  user=os.getenv('DB_USER'),
                  password=os.getenv('DB_PASSWORD'),
                  database=os.getenv('DB_NAME')
                )
              except: exit(1)
          initialDelaySeconds: 30
          periodSeconds: 300
      volumes:
      - name: logs
        emptyDir: {}
      - name: backups
        emptyDir: {}
      restartPolicy: Always
"""

def display_docker_setup():
    """Display Docker deployment instructions."""
    
    print("\n" + "="*80)
    print("DOCKER DEPLOYMENT FOR AQI COLLECTOR")
    print("="*80 + "\n")
    
    print("OPTION 1: Integration with Existing docker-compose.yml")
    print("-"*80)
    print("\n1. Add the following service to your docker-compose.yml:\n")
    print(DOCKER_SERVICE_YAML)
    
    print("\n2. Create Dockerfile.collector:\n")
    print(DOCKERFILE_COLLECTOR)
    
    print("\n3. Build and start:\n")
    print("   docker-compose up --build aqi-collector\n")
    
    print("\nOPTION 2: Standalone Docker Compose")
    print("-"*80)
    print("\n1. Create docker-compose.collector.yml with:\n")
    print(DOCKER_COMPOSE_STANDALONE)
    
    print("\n2. Start collector with database:\n")
    print("   docker-compose -f docker-compose.collector.yml up --build\n")
    
    print("\nOPTION 3: Kubernetes Deployment")
    print("-"*80)
    print("\n1. Create vayuguard-aqi-collector-deployment.yaml:\n")
    print(KUBE_DEPLOYMENT_YAML)
    
    print("\n2. Deploy to Kubernetes:\n")
    print("   kubectl apply -f vayuguard-aqi-collector-deployment.yaml\n")
    
    print("="*80)
    print("DOCKER COMMANDS")
    print("="*80 + "\n")
    
    print("View container logs:")
    print("   docker logs -f vayuguard-aqi-collector\n")
    
    print("View collection logs:")
    print("   docker exec vayuguard-aqi-collector tail -f data-pipeline/logs/collector_*.log\n")
    
    print("View data in database:")
    print("   docker exec -it vayuguard-postgres psql -U vayuguard_user -d vayuguard -c 'SELECT * FROM aqi_data ORDER BY created_at DESC LIMIT 5;'\n")
    
    print("Run manual collection:")
    print("   docker exec vayuguard-aqi-collector python -c 'import os; os.environ[\"RUN_ONCE\"]=\"1\"' && docker exec vayuguard-aqi-collector python collector.py\n")
    
    print("Stop collector:")
    print("   docker stop vayuguard-aqi-collector\n")
    
    print("Remove collector:")
    print("   docker rm vayuguard-aqi-collector\n")
    
    print("="*80)
    print("ENVIRONMENT VARIABLES")
    print("="*80 + "\n")
    
    print("Ensure these are set in your .env file:")
    print("  WAQI_API_KEY=<your_key>")
    print("  DB_HOST=postgres")
    print("  DB_PORT=5432")
    print("  DB_NAME=vayuguard")
    print("  DB_USER=vayuguard_user")
    print("  DB_PASSWORD=vayuguard_pass\n")
    
    print("="*80)
    print("HEALTH CHECKS")
    print("="*80 + "\n")
    
    print("The collector includes health checks that verify:")
    print("  ✅ Database connectivity")
    print("  ✅ API key availability")
    print("  ✅ Log file access\n")
    
    print("View health status:")
    print("   docker ps --filter 'name=vayuguard-aqi-collector'\n")
    
    print("="*80)
    print("SCALING")
    print("="*80 + "\n")
    
    print("For Kubernetes, scale replicas:")
    print("   kubectl scale deployment vayuguard-aqi-collector --replicas=3\n")
    
    print("For Docker Swarm:")
    print("   docker service create --replicas 3 --name vayuguard-aqi-collector vayuguard-aqi-collector:latest\n")
    
    print("="*80 + "\n")


if __name__ == '__main__':
    display_docker_setup()
