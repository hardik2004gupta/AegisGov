FROM python:3.12-slim AS base

# Create non-root user
RUN groupadd --system aegis && useradd --system --gid aegis --no-create-home aegis

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app ./app

# Set ownership
RUN chown -R aegis:aegis /app

USER aegis

EXPOSE 8000

# Health endpoint for Docker health checks
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
