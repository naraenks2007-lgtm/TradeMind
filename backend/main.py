import os
import sys
from pathlib import Path

# Ensure project root is always in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.api import health, market, hypothesis, memory, paper_trading, experiment, loop, upstox, replay, conversations

# Set UTF-8 encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

app = FastAPI(
    title="TradeMind AI - Intelligent Market Hypothesis & Memory Engine",
    description="Quantitative trading hypothesis generator powered by Groq LLM and Vectorize Hindsight long-term memory.",
    version="1.0.0"
)

# CORS Middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(market.router)
app.include_router(hypothesis.router)
app.include_router(memory.router)
app.include_router(paper_trading.router)
app.include_router(experiment.router)
app.include_router(loop.router)
app.include_router(upstox.router)
app.include_router(replay.router)
app.include_router(conversations.router)

# Mount frontend build if available
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Ignore api paths
        if full_path.startswith("api"):
            return None
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    def root():
        return {
            "app": "TradeMind AI Engine",
            "status": "online",
            "documentation": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
