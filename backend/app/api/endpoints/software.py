from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.software import Software, SoftwareCreate, SoftwarePublic, SoftwareSync, SoftwareUpdate
from app.models.utils import ensure, now


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Software)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=SoftwarePublic)
def get_by_id(db: DbSession, id: int): 
    db_software = db.get(Software, id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Software with {id} not found!")
    return db_software


@router.get("/{name}", response_model=SoftwarePublic)
def get_by_name(db: DbSession, name: str):
    db_software = db.exec(select(Software).where(Software.name == name)).first()
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Software with {name} not found!")
    return db_software


def sync_software(db: DbSession, software: SoftwareSync):
    db_software = db.exec(select(Software).where(Software.name == software.name)).first()
    
    if not db_software:
        create(db, SoftwareCreate(name=software.name))
    else:
        update(db, ensure(db_software.id), SoftwareUpdate(name=software.name))


def create(db: DbSession, software: SoftwareCreate):
    db_software = Software.model_validate(software)
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software


def update(db: DbSession, id: int, software: SoftwareUpdate):
    db_software = db.get(Software, id)
    if not db_software:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Software with {id} not found!")
    software_data = software.model_dump(exclude_unset=True)
    db_software.sqlmodel_update(software_data)
    db_software.modified_at = now()
    db.add(db_software)
    db.commit()
    db.refresh(db_software)
    return db_software
