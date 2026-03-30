# Backend

### Project setup

- Run `uv sync` to pull packages and .venv (note you have to have uv installed globally)

- For migrations run `alembic upgrade head` and `alembic revision --autogenerate -m "msg"` for revisions in the .venv

### Dropping and migrating

- Run `alembic downgrade base` to drop all
- Run `alembic upgrade head` to migrate and seed
