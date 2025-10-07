from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from sqlalchemy import create_engine
from app.core.config import settings

CONNECT_ARGS = {"check_same_thread": False} if settings.DB_DRIVER == "sqlite" else {}
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, connect_args=CONNECT_ARGS)

def get_session():
    with Session(engine) as session:
        yield session

DbSession = Annotated[Session, Depends(get_session)]