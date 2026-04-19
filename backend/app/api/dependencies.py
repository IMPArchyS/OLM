from datetime import datetime
from typing import Annotated, NoReturn
from fastapi import Depends, HTTPException, WebSocket, WebSocketException, status, Header, Query
from pydantic import BaseModel
from sqlmodel import Session
from sqlalchemy import create_engine
from app.core.config import settings
import httpx


class AuthUser(BaseModel):
    id: int
    username: str
    name: str
    admin: bool
    role_id: int
    deleted_at: datetime | None = None
    access_token: str = ""  


CONNECT_ARGS = {"check_same_thread": False} if settings.DB_DRIVER == "sqlite" else {}
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, connect_args=CONNECT_ARGS)

def get_session():
    with Session(engine) as session:
        yield session


def raise_auth_exception(status_code: int, detail: str, websocket: WebSocket | None) -> NoReturn:
    if websocket is not None:
        if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=detail)
        if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise WebSocketException(code=status.WS_1013_TRY_AGAIN_LATER, reason=detail)
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason=detail)

    raise HTTPException(status_code=status_code, detail=detail)


def get_token_from_authorization(authorization: str | None, websocket: WebSocket | None) -> str:
    if not authorization:
        raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Authorization header missing", websocket)
    try:
        scheme, token = authorization.split(maxsplit=1)
        if scheme.lower() != "bearer":
            raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid authentication scheme", websocket)
    except ValueError:
        raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid authorization header format", websocket)
    return token


async def validate_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/validate-token",
            json={"jwt_token": token},
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=5.0
        )
        response.raise_for_status()
        return response.json()


async def check_permission(jwt_token: str, permission: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/check-permission",
            json={"jwt_token": jwt_token, "permission": permission},
            headers={"x-api-key": settings.AUTH_API_KEY},
        )
        data = response.json()
        return data["valid"]


async def check_permissions(jwt_token: str, permissions: list[str]) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AUTH_SERVICE_URL}/check-permissions",
            json={"jwt_token": jwt_token, "permissions": permissions},
            headers={"x-api-key": settings.AUTH_API_KEY},
        )
        resp.raise_for_status()
        return resp.json()


async def get_user(token: str, websocket: WebSocket | None = None) -> AuthUser:
    try:
        data = await validate_token(token)
        if not data.get("valid"):
            raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", websocket)
        data["user"]["access_token"] = token
        return AuthUser.model_validate(data["user"])
    except httpx.HTTPStatusError:
        raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token", websocket)
    except httpx.RequestError:
        raise_auth_exception(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth service unavailable", websocket)
    except KeyError:
        raise_auth_exception(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid response from auth service", websocket)


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> AuthUser:
    token = get_token_from_authorization(authorization, None)
    return await get_user(token, None)


async def get_current_user_ws(websocket: WebSocket, access_token: Annotated[str | None, Query()] = None)  -> AuthUser:
    if not access_token:
        raise_auth_exception(status.HTTP_401_UNAUTHORIZED, "Access token missing", websocket)
    return await get_user(access_token, websocket)



def require_permission(permission: str):
    async def checker(user: AuthUser = Depends(get_current_user)):
        allowed = await check_permission(user.access_token, permission)
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker


def require_permission_ws(permission: str):
    async def checker(
        websocket: WebSocket,
        user: AuthUser = Depends(get_current_user_ws),
    ) -> AuthUser:
        try:
            allowed = await check_permission(user.access_token, permission)
        except httpx.RequestError:
            raise_auth_exception(status.HTTP_503_SERVICE_UNAVAILABLE, "Auth service unavailable", websocket)
        except KeyError:
            raise_auth_exception(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invalid response from auth service", websocket)

        if not allowed:
            raise_auth_exception(status.HTTP_403_FORBIDDEN, "Forbidden", websocket)

        return user

    return checker


def PermissionWs(permission: str) -> AuthUser:
    return Depends(require_permission_ws(permission))


def Permission(permission: str) -> AuthUser:
    return Depends(require_permission(permission))

DbSession = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
CurrentUserWs = Annotated[AuthUser, Depends(get_current_user_ws)]