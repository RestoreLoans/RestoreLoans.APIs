FROM python:3.12.15 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN python -m venv .venv
COPY requirements.txt ./
# psycopg2-binary ships prebuilt wheels with libpq bundled, so no system
# libpq/gcc is required at build time or runtime.
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.12.15-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .
CMD /app/.venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 --access-logfile -
