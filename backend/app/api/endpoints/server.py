from typing import List
from fastapi import APIRouter, HTTPException, status
import httpx
from sqlmodel import select
from app.api.dependencies import DbSession

from app.api.endpoints.sync import sync_add_server_stack
from app.models.device import DevicePublic, DeviceWithSoftware
from app.models.server import Server, ServerCreate, ServerPublic, ServerPubDetailed, ServerUpdate
from app.models.utils import now
from app.core.config import settings

# ServerPubDetailed.model_rebuild()


router = APIRouter()


def resolve_url(server: Server):
    api_domain = (getattr(server, "api_domain", None) or "").strip()
    if not api_domain:
        return None

    if api_domain in ("127.0.0.1", "localhost"):
        api_domain = "host.docker.internal"

    scheme = "https" if getattr(server, "https", False) else "http"
    port = getattr(server, "port", None)

    base_url = f"{scheme}://{api_domain}"
    if port:
        base_url = f"{base_url}:{port}"
    
    return base_url


def ping_remote_server(db: DbSession, server: ServerPublic, health_url: str):
    available = False
    try:
        response = httpx.get(health_url, headers={"x-api-key": settings.EXPERIMENTAL_API_KEY})
        if response.status_code < 400:
            body = response.json()

            if body["status"] == "ok":
                available = True
                devices = body.get("devices", [])
                sync_add_server_stack(db, server, devices)
    except httpx.RequestError:
        available = False

    return available


@router.post("/{id}/sync", status_code=status.HTTP_200_OK)
def sync(db: DbSession, id: int):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")

    health_url = resolve_url(db_server)
    if not health_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Server missing domain!")
    
    health_url += "/api/server/sync"
    db_server.available = ping_remote_server(db, ServerPublic.model_validate(db_server), health_url)

    db.add(db_server)
    db.commit()
    db.refresh(db_server)

    return {
        "id": db_server.id,
        "available": db_server.available,
    }


@router.post("/sync_all", status_code=status.HTTP_200_OK)
def sync_all(db: DbSession):
    servers = db.exec(select(Server)).all()
    
    results = []
    for db_server in servers:
        health_url = resolve_url(db_server)
        if not health_url:
            results.append({"id": db_server.id, "available": False, "error": "Server missing domain"})
            continue
        
        health_url += "/api/server/sync"
        db_server.available = ping_remote_server(db, ServerPublic.model_validate(db_server), health_url)

        db.add(db_server)
        db.commit()
        results.append(
            {
                "id": db_server.id,
                "available": db_server.available,
            }
        )
    
    return results


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


@router.get("/{id}/devices", response_model=List[DeviceWithSoftware])
def get_server_devices(db: DbSession, id: int):
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


@router.patch("/{id}", response_model=ServerUpdate)
def update(db: DbSession, id: int, server: ServerUpdate):
    db_server = db.get(Server, id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {id} not found!")
    server_data = server.model_dump(exclude_unset=True)
    db_server.sqlmodel_update(server_data)
    db_server.modified_at = now()
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(db: DbSession, id: int):
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