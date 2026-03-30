from typing import Annotated, NoReturn
from fastapi import Depends, HTTPException, WebSocket, WebSocketException, status, Header, Query
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


def _raise_auth_exception(
    *,
    detail: str,
    status_code: int,
    websocket: WebSocket | None,
) -> NoReturn:
    if websocket is not None:
        if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=detail)
        if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise WebSocketException(code=status.WS_1013_TRY_AGAIN_LATER, reason=detail)
        raise WebSocketException(code=status.WS_1011_INTERNAL_ERROR, reason=detail)

    raise HTTPException(status_code=status_code, detail=detail)


def _get_token_from_authorization(
    authorization: str | None,
    websocket: WebSocket | None,
) -> str:
    if not authorization:
        logger.warning("Authorization attempt failed: Authorization header missing")
        _raise_auth_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            websocket=websocket,
        )

    assert authorization is not None

    try:
        scheme, token = authorization.split(maxsplit=1)
        if scheme.lower() != "bearer":
            logger.warning(f"Authorization attempt failed: Invalid authentication scheme '{scheme}'")
            _raise_auth_exception(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                websocket=websocket,
            )
    except ValueError:
        logger.warning(f"Authorization attempt failed: Invalid authorization header format: {authorization[:50]}")
        _raise_auth_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            websocket=websocket,
        )

    return token


def _validate_token_and_get_user_id(token: str, websocket: WebSocket | None = None) -> int:
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
            _raise_auth_exception(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                websocket=websocket,
            )
        
        return data["user"]["id"]
    except httpx.HTTPStatusError as e:
        logger.error(f"Authorization attempt failed: HTTP error from auth service: {e}, Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
        _raise_auth_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            websocket=websocket,
        )
    except httpx.RequestError as e:
        logger.error(f"Authorization attempt failed: Auth service unavailable: {e}")
        _raise_auth_exception(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
            websocket=websocket,
        )
    except KeyError as e:
        logger.error(f"Authorization attempt failed: Invalid response from auth service, missing key: {e}")
        _raise_auth_exception(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid response from auth service",
            websocket=websocket,
        )


def get_current_user_id(authorization: Annotated[str | None, Header()] = None) -> int:
    token = _get_token_from_authorization(authorization, websocket=None)
    return _validate_token_and_get_user_id(token, websocket=None)


def get_current_user_id_ws(
    websocket: WebSocket,
    access_token: Annotated[str | None, Query()] = None,
) -> int:
    # Browsers cannot set custom Authorization headers in new WebSocket(...).
    token = access_token or websocket.query_params.get("access_token") or ""

    if not token:
        logger.warning("Authorization attempt failed: access_token query parameter missing")
        _raise_auth_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token missing",
            websocket=websocket,
        )

    return _validate_token_and_get_user_id(token, websocket=websocket)


CurrentUserId = Annotated[int, Depends(get_current_user_id)]
CurrentUserIdWs = Annotated[int, Depends(get_current_user_id_ws)]