FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

# Build deps for psycopg; removed again to keep the image small.
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y build-essential && apt-get autoremove -y

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN useradd --create-home --uid 10001 soiltax && chown -R soiltax:soiltax /srv/app
USER soiltax

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -fsS http://localhost:8000/health || exit 1

# Migrations are run as a separate step (`alembic upgrade head`) rather than on
# container start, so a rolling deploy never races two migrating replicas.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
