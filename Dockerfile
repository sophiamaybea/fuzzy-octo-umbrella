FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HUNTER_DATABASE=/tmp/capability-hunter.sqlite3
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd -u 10001 --create-home worker
USER worker
EXPOSE 8000
CMD ["sh", "-c", "uvicorn capability_hunter.server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
