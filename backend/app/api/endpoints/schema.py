from fastapi import APIRouter, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device
from app.models.device_type import DeviceType, DeviceTypeCreate
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema, SchemaCreate, SchemaPublic, SchemaUpdate
from app.models.server import Server


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Schema)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=SchemaPublic)
def get_by_id(db: DbSession, id: int): 
    db_schema = db.get(Schema, id)
    if not db_schema:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return db_schema

@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, schema: SchemaCreate):
    db_schema = Schema.model_validate(schema)
    db.add(db_schema)
    db.commit()
    db.refresh(db_schema)
    return db_schema


@router.patch("/{id}", response_model=SchemaUpdate)
def update(db: DbSession, id: int, schema: SchemaUpdate):
    db_schema = db.get(Schema, id)
    if not db_schema:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    schema_data = schema.model_dump(exclude_unset=True)
    db_schema.sqlmodel_update(schema_data)
    db.add(db_schema)
    db.commit()
    db.refresh(db_schema)
    return db_schema


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_schema = db.get(Schema, id)
    if not db_schema:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(db_schema)
    db.commit()
    return db_schema