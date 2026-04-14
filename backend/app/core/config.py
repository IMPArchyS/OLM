from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
def is_empty(value: str | None) -> bool:
    return value is None or value == ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    DB_DRIVER: str = "postgresql"
    DB_HOST: str = "localhost"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_PORT: str | int | None = None
    DB_PATH: str | None = None

    AUTH_SERVICE_URL: str = "http://host.docker.internal:8080/internal/api" # "http://node124.webte.fei.stuba.sk:8080/internal/api"
    OAUTH_SERVICE_URL: str = "http://host.docker.internal:8080/api/auth/oauth"
    AUTH_API_KEY: str = "devapikey"
    EXPERIMENTAL_API_KEY: str = "experimentalapikey"
    EXPERIMENT_QUEUE_WORKER_ENABLED: bool = True
    EXPERIMENT_QUEUE_WORKER_INTERVAL_SECONDS: int = 5
    EXPERIMENT_QUEUE_REQUEST_TIMEOUT_SECONDS: float = 10.0
    EXPERIMENT_QUEUE_BATCH_SIZE: int = 20
    EXPERIMENT_QUEUE_RETRY_BASE_SECONDS: int = 30
    EXPERIMENT_QUEUE_RETRY_MAX_SECONDS: int = 600
    EXPERIMENT_QUEUE_POLL_INTERVAL_SECONDS: int = 5
    EXPERIMENT_QUEUE_SUBMIT_PATH: str = "/api/server/experiments/queue"
    EXPERIMENT_QUEUE_STATUS_PATH: str = "/api/server/experiments/{job_id}"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        host = f"/{self.DB_HOST}" if self.DB_DRIVER == "sqlite" else self.DB_HOST
        port = int(self.DB_PORT) if self.DB_PORT is not None else None
        return str(
            MultiHostUrl.build(
                scheme=self.DB_DRIVER,
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=host,
                port=port,
                path=self.DB_PATH,
            )
        )


settings = Settings()