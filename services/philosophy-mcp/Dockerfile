FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY philosophy_core.py server.py ./
# STDIO by default. Never expose a publicly unauthenticated MCP endpoint.
CMD ["python", "server.py"]
