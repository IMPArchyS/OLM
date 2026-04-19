from typing import Annotated
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import httpx

from app.api.dependencies import CurrentUser
from app.core.config import settings
from app.models.auth import (
    ChangeNameRequest, 
    ChangePasswordRequest, 
    LoginRequest, 
    PermissionRequest,
    PermissionResponse,
    ProviderResponse,
    RegisterRequest,
    TokenResponse
)
from app.models.utils import now


router = APIRouter()


def _auth_error_payload(response: httpx.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return {"detail": text or "Auth service returned an empty error response"}

    if isinstance(payload, dict):
        return payload

    return {"detail": payload}


def calc_max_age(expires_at: str | datetime) -> int:
    if isinstance(expires_at, datetime):
        expiry = expires_at
    else:
        normalized = expires_at.strip()
        if normalized.endswith("Z"):
            normalized = f"{normalized[:-1]}+00:00"
        expiry = datetime.fromisoformat(normalized)

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    else:
        expiry = expiry.astimezone(timezone.utc)

    delta = expiry - now()
    return max(0, int(delta.total_seconds()))


@router.post("/register", response_model=TokenResponse)
async def register(credentials: RegisterRequest, response: Response):
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/register",
                json={
                    "name": credentials.name,
                    "username": credentials.username,
                    "password": credentials.password
                },
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        auth_response.raise_for_status()
        token_data = auth_response.json()
        
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=calc_max_age(token_data["refresh_token_expires_at"]),
            path="/"
        )
        
        return token_data
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, response: Response):
    try:
        async with httpx.AsyncClient() as client:
            auth_response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/login",
                json={"username": credentials.username, "password": credentials.password, "remember_me": credentials.remember_me},
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        auth_response.raise_for_status()
        token_data = auth_response.json()
        
        response.set_cookie(
            key="refresh_token",
            value=token_data["refresh_token"],
            httponly=True,  
            secure=False,  
            samesite="lax",
            max_age=calc_max_age(token_data["refresh_token_expires_at"]),
            path="/"
        )
        
        return token_data
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    try:
        async with httpx.AsyncClient() as client: 
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/refresh",  
                json={"refresh_token": refresh_token},
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"REFRESH Failed to connect to auth service: {str(e)}"
        )


@router.post("/session")
async def get_session(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/refresh",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"refresh_token": refresh_token}
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return response.json()


@router.post("/logout")
async def logout(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/logout",  
                json={"refresh_token": refresh_token},
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LOGOUT Failed to connect to auth service: {str(e)}"
        )


@router.post("/validate-token")
async def validate_token(jwt_token: Annotated[str, Cookie(alias="refresh_token")]):
    if not jwt_token:
        raise HTTPException(status_code=401, detail="No jwt token")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/validate-token",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"jwt_token": jwt_token}
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return response.json()


@router.post("/check-permission")
async def check_permission(perm_request: PermissionRequest) -> bool:
    if not perm_request.jwt_token:
        raise HTTPException(status_code=401, detail="No jwt token")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/check-permission",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"jwt_token": perm_request.jwt_token, "permission": perm_request.permission}
        )
    
    data = response.json()
    return data["valid"]


@router.get("/permissions", response_model=PermissionResponse)
async def get_permissions(user: CurrentUser):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/users/{user.id}/permissions",
                headers={"X-Api-Key": settings.AUTH_API_KEY},
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PROVIDERS Failed to connect to auth service: {str(e)}"
        ) 


@router.get("/providers", response_model=list[ProviderResponse])
async def get_oath_providers():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/providers",
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PROVIDERS Failed to connect to auth service: {str(e)}"
        ) 


@router.get("/user/{id}")
async def get_user_by_id(id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/users/{id}",
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        )


@router.patch("/update-user")
async def update_username(credentials: ChangeNameRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.AUTH_SERVICE_URL}/update-user",
                json={"jwt_token": credentials.jwt_token, "name": credentials.name},
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        )


@router.patch("/change-password")
async def change_password(credentials: ChangePasswordRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{settings.AUTH_SERVICE_URL}/change-password",
                json={"jwt_token": credentials.jwt_token, "password_old": credentials.password_old, 
                    "password_new": credentials.password_new, "password_new_repeat": credentials.password_new_repeat},
                headers={"x-api-key": settings.AUTH_API_KEY},
                timeout=10.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content=_auth_error_payload(e.response)
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        ) 