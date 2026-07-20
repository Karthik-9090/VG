# Run FastAPI with Uvicorn in single-worker mode
# Uvicorn handles concurrency natively via async/await

import uvicorn
import multiprocessing

if __name__ == "__main__":
    # Single-worker mode with aggressive thread pool for CPU-bound inference
    # Multiprocessing on Windows causes overhead that reduces throughput
    # Solution: Keep single event loop, maximize thread parallelism (256+ workers)
    uvicorn.run(
        "app_production:app",
        host="127.0.0.1",
        port=8001,
        workers=1,  # Single worker to avoid multiprocessing overhead on Windows
        loop="asyncio",  # Use asyncio (uvloop not available on Windows)
        access_log=True,
        log_level="info"
    )
