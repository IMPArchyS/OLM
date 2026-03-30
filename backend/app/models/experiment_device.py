from sqlmodel import Field, SQLModel


class ExperimentDevice(SQLModel, table=True):
    __tablename__ = "experiment_device"  # type: ignore

    experiment_id: int | None = Field(foreign_key="experiment.id", primary_key=True)
    device_id: int | None = Field(foreign_key="device.id", primary_key=True)
