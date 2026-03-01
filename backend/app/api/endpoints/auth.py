from typing import Annotated
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from pydantic import BaseModel
from datetime import datetime

import httpx

from app.core.config import settings


router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    refresh_token_expires_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    name: str  
    username: str
    password: str

class ProviderResponse(BaseModel):
    id: int
    name: str
    display_name: str
    logo_url: str


class LogoutReponse(BaseModel):
    success: bool


@router.post("/register", response_model=TokenResponse)
def register(credentials: RegisterRequest, response: Response):
    try:
        auth_response = httpx.post(
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
            key="olm_refresh_token",
            value=token_data["refresh_token"],
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60,
            path="/"
        )
        
        return token_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Registration error: {e.response.text}"
        )


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, response: Response):
    try:
        auth_response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/login",
            json={"username": credentials.username, "password": credentials.password},
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        auth_response.raise_for_status()
        token_data = auth_response.json()
        
        response.set_cookie(
            key="olm_refresh_token",
            value=token_data["refresh_token"],
            httponly=True,  
            secure=False,  
            samesite="lax",
            max_age=60 * 60, 
            path="/"
        )
        
        return token_data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"LOGIN Auth service error: {e.response.text}"
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: Annotated[str, Cookie(alias="olm_refresh_token")]):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    try:
        response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/refresh",  
            json={"refresh_token": refresh_token},
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"REFRESH Auth service error: {e.response.text}"
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
            f"{settings.AUTH_SERVICE_URL}/internal/api/refresh",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"refresh_token": refresh_token}
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return response.json()

@router.post("/logout")
def logout(refresh_token: Annotated[str, Cookie(alias="olm_refresh_token")]):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    try:
        response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/logout",  
            json={"refresh_token": refresh_token},
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"LOGOUT Auth service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LOGOUT Failed to connect to auth service: {str(e)}"
        )


@router.post("/validate-token")
async def validate_token(jwt_token: Annotated[str, Cookie(alias="olm_refresh_token")]):
    if not jwt_token:
        raise HTTPException(status_code=401, detail="No jwt token")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/internal/api/validate-token",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"jwt_token": jwt_token}
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return response.json()


@router.post("/check-permissions")
async def check_permissions(jwt_token: Annotated[str, Cookie(alias="olm_refresh_token")], perms: list[str]):
    if not jwt_token:
        raise HTTPException(status_code=401, detail="No jwt token")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AUTH_SERVICE_URL}/internal/api/check-permissions",
            headers={"X-Api-Key": settings.AUTH_API_KEY},
            json={"jwt_token": jwt_token, "permissions": perms}
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return response.json()


@router.get("/providers", response_model=list[ProviderResponse])
def get_oath_providers():
    try:
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/providers",
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"PROVIDERS Auth service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PROVIDERS Failed to connect to auth service: {str(e)}"
        ) 


@router.get("/user/{id}")
def get_user_by_id(id: int):
    try:
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/users/{id}",
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"USERS/ID Auth service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        )


@router.get("/user/{id}/with-role")
def get_user_with_role(id: int):
    try:
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/users/{id}/with-role",
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"USERS/ID Auth service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        )


@router.get("/user/{id}/permissions")
def get_user_permissions(id: int):
    try:
        response = httpx.get(
            f"{settings.AUTH_SERVICE_URL}/users/{id}/permissions",
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"USERS/ID Auth service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"USERS/ID Failed to connect to auth service: {str(e)}"
        )
