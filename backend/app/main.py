from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api.api import api_router

logger = logging.getLogger(__name__)

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    method = request.scope.get("method", "websocket")
    path = request.scope.get("path", str(request.url.path))
    client = request.client.host if request.client else "unknown"

    logger.error(
        f"HTTPException: {exc.status_code} {exc.detail} | "
        f"Method: {method} | "
        f"URL: {path} | "
        f"Client: {client}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)