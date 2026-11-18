# Build context must be the repo root:
#   podman build -f backend/Dockerfile -t sommebeer-api .
#   docker  build -f backend/Dockerfile -t sommebeer-api .
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# backend/requirements.txt references ../requirements.txt, hence repo-root context
COPY requirements.txt backend/requirements.txt /tmp/
RUN pip install -r /tmp/backend/requirements.txt

FROM python:3.12-slim

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY sommebeer/ sommebeer/
COPY backend/ backend/

# app.state.graph is built at startup; runs as unprivileged user
RUN useradd --system --create-home sommebeer \
    && chown -R sommebeer:sommebeer /app
USER sommebeer

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

# SOMMEBEER_* settings arrive via env (config.py has env_prefix="SOMMEBEER_")
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
