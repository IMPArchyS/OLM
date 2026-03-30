from datetime import datetime
from typing import TYPE_CHECKING, Any
from pydantic import BaseModel
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from app.models.utils import now
from app.models.experiment import Command

if TYPE_CHECKING:
    from app.models.experiment import Experiment


class PydanticJSONB(TypeDecorator):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        def to_jsonable(obj):
            if isinstance(obj, BaseModel):
                return obj.model_dump(mode="json")
            if isinstance(obj, list):
                return [to_jsonable(item) for item in obj]
            if isinstance(obj, dict):
                return {key: to_jsonable(item) for key, item in obj.items()}
            return obj

        return to_jsonable(value)


class ExperimentInputHistoryItem(BaseModel):
    command: Command
    input_args: dict[str, Any]
    


class ExperimentRun(BaseModel):
    input_history: list[ExperimentInputHistoryItem]
    output_history: list[dict[str, Any]]


class ExperimentLogBase(SQLModel):
    # Field(default=None, sa_column=Column(PydanticJSONB)) 
    run: ExperimentRun | None = Field(default=None, sa_type=JSONB)
    note: str | None = Field(default=None, index=True)


class ExperimentLog(ExperimentLogBase, table=True):
    __tablename__ = "experiment_log" # type: ignore
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=None)
    
    created_at: datetime = Field(default_factory=now)
    modified_at: datetime = Field(default_factory=now)
    deleted_at: datetime | None = Field(default=None)
    
    started_at: datetime = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    stopped_at: datetime | None = Field(default=None)
    timedout_at: datetime | None = Field(default=None)
    
    # Relationships
    experiment_id: int = Field(foreign_key="experiment.id")
    experiment: "Experiment" = Relationship(back_populates="experiment_logs")


class ExperimentLogCreate(ExperimentLogBase):
    user_id: int
    experiment_id: int


class ExperimentLogPublic(ExperimentLogBase):
    id: int
    user_id: int
    started_at: datetime
    modified_at: datetime
    deleted_at: datetime | None


class ExperimentLogUpdate(ExperimentLogBase):
    finished_at: datetime 