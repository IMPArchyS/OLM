from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.software import Software, SoftwarePublic


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
