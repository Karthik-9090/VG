# Build stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev --fetch-retries=10 --network-timeout=200000

# Production stage
FROM node:20-slim
WORKDIR /app
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
COPY server.js ./
COPY db.js ./
COPY config.js ./
COPY middleware ./middleware
COPY routes ./routes
COPY services ./services

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
ENV NODE_ENV=production
ENV PORT=5000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["node", "--trace-warnings", "--max-old-space-size=512", "server.js"]
