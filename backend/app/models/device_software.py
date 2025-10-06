from sqlmodel import Field, SQLModel


class DeviceSoftware(SQLModel, table=True):
    __tablename__ = "device_software"  # type: ignore
    device_id: int | None = Field(foreign_key="device.id", primary_key=True)
    software_id: int | None = Field(foreign_key="software.id", primary_key=True)