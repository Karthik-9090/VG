FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --no-cache-dir --timeout 100 --retries 10 -r requirements.txt

COPY . /app

CMD ["python", "scheduler.py"]
