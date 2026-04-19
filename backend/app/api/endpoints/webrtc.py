from fastapi import APIRouter, HTTPException, status
from urllib.parse import quote
from fastapi.responses import JSONResponse
import httpx
from sqlmodel import SQLModel
from app.api.dependencies import AuthUser, DbSession, Permission
from app.api.endpoints.server import resolve_url
from app.core.config import settings
from app.models.server import Server


router = APIRouter()
HTTP_TIMEOUT_SECONDS = 10.0


class GrantTimeRequest(SQLModel):
    ttl_seconds: int


class GrantRefreshRequest(SQLModel):
    grant_token: str


@router.post("/{server_id}/{device_name}/grants")
def get_device_webrtc_grant(db: DbSession, server_id: int, device_name: str, _: AuthUser = Permission("olm.sandbox.stream")):
    health_url = check_device_server_url(db, server_id)

    health_url += f"/api/server/devices/{quote(device_name)}/webrtc/grants"
    try:
        response = httpx.post(
            health_url,
            headers={"device_name": device_name, "x-api-key": settings.EXPERIMENTAL_API_KEY},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to experimental service: {str(e)}",
        )



@router.post("/{server_id}/{device_name}/grants/refresh")
def refresh_device_webrtc_grant(db: DbSession, server_id: int, device_name: str, grant_token: GrantRefreshRequest, _: AuthUser = Permission("olm.sandbox.stream")):
    health_url = check_device_server_url(db, server_id)

    health_url += f"/api/server/devices/{quote(device_name)}/webrtc/grants/refresh"
    try:
        response = httpx.post(
            health_url,
            headers={"device_name": device_name, "x-api-key": settings.EXPERIMENTAL_API_KEY},
            json=grant_token.model_dump(),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=e.response.json()
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to experimental service: {str(e)}",
        )


def check_device_server_url(db: DbSession, server_id: int) -> str:
    db_server = db.get(Server, server_id)
    if not db_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Server with {server_id} not found!")

    health_url = resolve_url(db_server)
    if not health_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Server with {server_id} missing api domain!")

    return health_url
