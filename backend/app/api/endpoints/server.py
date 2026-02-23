from typing import List
from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select
from app.api.dependencies import DbSession

from app.models.device import Device, DevicePublic
from app.models.device_type import DeviceType
from app.models.device_software import DeviceSoftware
from app.models.software import Software
from app.models.experiment import Experiment
from app.models.reserved_experiment import ReservedExperiment
from app.models.schema import Schema
from app.models.server import Server, ServerCreate, ServerPublic, ServerPubDetailed, ServerUpdate
from app.models.utils import now
import httpx


ServerPubDetailed.model_rebuild()


router = APIRouter()


@router.get("/")
def get_all(db: DbSession): 
    stmt = select(Server)
    return db.exec(stmt).all()


@router.get("/{id}", response_model=ServerPublic)
def get_by_id(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    return db_server


@router.get("/{id}/devices", response_model=List[DevicePublic])
def get_by_devices_by_server(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    return db_server.devices


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(db: DbSession, server: ServerCreate):
    db_server = Server.model_validate(server)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.post("/{id}/restore", status_code=status.HTTP_200_OK)
def restore(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    db_server.deleted_at = None
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.post("/{id}/sync", status_code=status.HTTP_200_OK)
def sync(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")

    ip_address = (getattr(db_server, "ip_address", None) or "").strip()
    if not ip_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server IP address is not configured",
        )

    if ip_address in ("127.0.0.1", "localhost"):
        ip_address = "host.docker.internal"

    scheme = "https" if getattr(db_server, "https", False) else "http"
    port = getattr(db_server, "websocket_port", None)

    base_url = f"{scheme}://{ip_address}"
    if port:
        base_url = f"{base_url}:{port}"

    health_url = f"{base_url}/api/server/health"

    db_server.available = False
    try:
        response = httpx.get(health_url)
        if response.status_code < 400:
            try:
                body = response.json()
            except ValueError as e:
                body = None

            if isinstance(body, dict) and body.get("status") == "ok":
                db_server.available = True

    except httpx.RequestError as e:
        db_server.available = False

    db.add(db_server)
    db.commit()
    db.refresh(db_server)

    return {"id": db_server.id, "available": db_server.available}


@router.post("/sync_all", status_code=status.HTTP_200_OK)
def sync_all(db: DbSession):
    stmt = select(Server)
    servers = db.exec(stmt).all()
    
    results = []
    for db_server in servers:
        ip_address = (getattr(db_server, "ip_address", None) or "").strip()
        if not ip_address:
            results.append({"id": db_server.id, "available": False, "error": "No IP address configured"})
            continue

        if ip_address in ("127.0.0.1", "localhost"):
            ip_address = "host.docker.internal"

        scheme = "https" if getattr(db_server, "https", False) else "http"
        port = getattr(db_server, "websocket_port", None)

        base_url = f"{scheme}://{ip_address}"
        if port:
            base_url = f"{base_url}:{port}"

        health_url = f"{base_url}/api/server/health"

        db_server.available = False
        try:
            response = httpx.get(health_url)
            if response.status_code < 400:
                try:
                    body = response.json()
                except ValueError as e:
                    body = None

                if isinstance(body, dict) and body.get("status") == "ok":
                    db_server.available = True

        except httpx.RequestError as e:
            db_server.available = False

        db.add(db_server)
        results.append({"id": db_server.id, "available": db_server.available})
    
    db.commit()
    return results

@router.patch("/{id}", response_model=ServerUpdate)
def update(db: DbSession, id: int, server: ServerUpdate):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    server_data = server.model_dump(exclude_unset=True)
    db_server.sqlmodel_update(server_data)
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    db.delete(db_server)
    db.commit()
    return None


@router.delete("/{id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    if db_server.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_410_GONE,detail="Server already deleted")
    db_server.deleted_at = now()
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return None