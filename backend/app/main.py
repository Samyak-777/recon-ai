"""
ReconAI — Main FastAPI Application Entrypoint
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import connect_db, close_db
from app.routers import recon, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="ReconAI",
    version=settings.VERSION,
    description="Autonomous Multi-Rail Settlement Reconciliation & Financial Controller (Razorpay AI Buildathon 2026 — Track 04)",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(recon.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {
        "status": "HEALTHY",
        "project": "ReconAI",
        "version": settings.VERSION,
        "track": "AI Finance Controller (Track 04)",
        "razorpay_connected": bool(settings.RAZORPAY_KEY_ID),
        "key_id": settings.RAZORPAY_KEY_ID[:12] + "..." if settings.RAZORPAY_KEY_ID else "NOT_SET"
    }
