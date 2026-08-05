FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --no-install-recommends --yes poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system alfil \
    && useradd --system --gid alfil --create-home alfil

WORKDIR /app

COPY requirements.txt ./
RUN pip install --requirement requirements.txt

COPY --chown=alfil:alfil app ./app

USER alfil

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os; from urllib.request import urlopen; urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/api/ready', timeout=3)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --proxy-headers --forwarded-allow-ips='*'"]
