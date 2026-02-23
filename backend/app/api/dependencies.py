from typing import Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlmodel import Session
from sqlalchemy import create_engine
from app.core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)

CONNECT_ARGS = {"check_same_thread": False} if settings.DB_DRIVER == "sqlite" else {}
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, connect_args=CONNECT_ARGS)

def get_session():
    with Session(engine) as session:
        yield session

DbSession = Annotated[Session, Depends(get_session)]

def get_current_user_id(authorization: str = Header(None)) -> int:
    if not authorization:
        logger.warning("Authorization attempt failed: Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            logger.warning(f"Authorization attempt failed: Invalid authentication scheme '{scheme}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        logger.warning(f"Authorization attempt failed: Invalid authorization header format: {authorization[:50]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )
    
    try:
        response = httpx.post(
            f"{settings.AUTH_SERVICE_URL}/validate-token",
            json={"jwt_token": token},
            headers={"x-api-key": settings.AUTH_API_KEY},
            timeout=5.0
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("valid"):
            logger.warning(f"Authorization attempt failed: Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return data["user"]["id"]
    except httpx.HTTPStatusError as e:
        logger.error(f"Authorization attempt failed: HTTP error from auth service: {e}, Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    except httpx.RequestError as e:
        logger.error(f"Authorization attempt failed: Auth service unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable"
        )
    except KeyError as e:
        logger.error(f"Authorization attempt failed: Invalid response from auth service, missing key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from auth service"
        )

CurrentUserId = Annotated[int, Depends(get_current_user_id)]