FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY packages/ packages/
COPY scripts/ scripts/
COPY examples/ examples/
COPY config/.env.example config/.env.example
CMD ["python", "scripts/run_validation.py", "--tenants", "examples/tenants.sample.json"]
