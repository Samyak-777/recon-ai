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


@app.get("/")
async def root():
    return {
        "project": "ReconAI",
        "status": "OPERATIONAL",
        "tagline": "Autonomous Settlement Reconciliation & Financial Intelligence",
        "track": "Razorpay AI Buildathon 2026 — Track 04: AI Finance Controller",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION,
        "endpoints": {
            "reconciliation": "/api/recon/results",
            "seed_batch": "/api/recon/seed",
            "run_pipeline": "/api/recon/run",
            "exceptions": "/api/recon/exceptions",
            "settlement_qa": "/api/recon/qa",
            "cash_forecast": "/api/recon/forecast",
            "tax_itc_dashboard": "/api/recon/tax-dashboard",
            "webhooks_listener": "/api/recon/webhooks",
            "webhooks_feed": "/api/recon/webhooks/feed"
        }
    }


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
