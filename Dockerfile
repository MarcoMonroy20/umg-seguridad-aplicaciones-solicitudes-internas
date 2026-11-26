FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.txt
COPY api.py .
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api:from_environment", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
