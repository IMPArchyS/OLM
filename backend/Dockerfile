FROM python:3.13

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen
RUN uv pip install alembic psycopg2-binary --system
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY alembic.ini .
COPY ./app ./app
COPY ./app/migrations ./app/migrations

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN echo '#!/bin/sh\n\
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do\n\
  echo "Waiting for database..."\n\
  sleep 2\n\
done\n\
echo "Database is ready!"\n\
alembic upgrade head\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]

EXPOSE 8000