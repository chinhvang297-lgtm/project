"""
NBA Prediction Agent System - FastAPI Application Entry Point.

A multi-agent AI system that predicts NBA game outcomes using
LangGraph workflow orchestration with 6 specialized agents.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.db.session import init_db
from app.core.logger import get_logger

logger = get_logger("main")

# Initialize database
init_db()

# Create FastAPI application
app = FastAPI(
    title="NBA Prediction Agent System",
    description="Multi-agent AI system for NBA game prediction using LangGraph",
    version="2.0.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "NBA Prediction Agent System v2.0",
        "docs": "/docs",
        "endpoints": {
            "predict": "POST /api/v1/predict",
            "history": "GET /api/v1/predictions",
            "evaluate": "POST /api/v1/evaluate/{id}",
            "stats": "GET /api/v1/stats",
            "health": "GET /api/v1/health",
        },
    }


if __name__ == "__main__":
    logger.info("Starting NBA Prediction Agent System v2.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)
