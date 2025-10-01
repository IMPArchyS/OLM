from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import workspace_router
from app.routers import tool_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspace_router.router)
app.include_router(tool_router.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Working"}
