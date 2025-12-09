"""Main FastAPI application."""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.assemble_map import router as assemble_map_router
from app.config import BACKEND_HOST, BACKEND_PORT

app = FastAPI(title="Wish Map Backend - Kolors MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assemble_map_router, prefix="/api", tags=["map"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "wish-map-backend"}


if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))
    uvicorn.run("app.api.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
