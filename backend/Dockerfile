FROM python:3.13

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen
RUN uv pip install alembic psycopg2-binary --system

COPY alembic.ini .
COPY ./app ./app
COPY ./app/migrations ./app/migrations

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

CMD /bin/sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

EXPOSE 8000