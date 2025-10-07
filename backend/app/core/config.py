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