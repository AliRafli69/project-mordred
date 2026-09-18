FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/mordred

RUN useradd \
    --create-home \
    --uid 10001 \
    --shell /usr/sbin/nologin \
    mordred

COPY requirements.txt requirements-dev.txt ./

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=mordred:mordred app ./app

COPY --chown=mordred:mordred prompts/system_prompt.txt ./prompts/system_prompt.txt

USER mordred

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=3s \
    --start-period=10s \
    --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]


FROM runtime AS test

USER root

RUN python -m pip install --no-cache-dir -r requirements-dev.txt

COPY --chown=mordred:mordred tests ./tests

USER mordred

CMD ["python", "-m", "pytest", "-q", "-o", "cache_dir=/tmp/pytest_cache"]
