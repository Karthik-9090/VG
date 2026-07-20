# Gunicorn configuration for production ML service
# Runs multiple Uvicorn workers to parallelize requests

import multiprocessing

# Number of workers = CPU cores * 2 (for concurrency)
cpu_cores = multiprocessing.cpu_count()
workers = max(2, cpu_cores * 2)

# Worker class: Uvicorn ASGI worker for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Binding
bind = "127.0.0.1:8001"

# Timeout (30 seconds for inference)
timeout = 30

# Keep-alive timeout
keepalive = 5

# Max requests per worker (restart worker after 1000 requests to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Worker connections (max concurrent connections per worker)
worker_connections = 1000

# Logging
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

print(f"Gunicorn config: {workers} workers, worker_class={worker_class}")
