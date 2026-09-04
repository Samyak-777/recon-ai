"""
ReconAI Configuration — Settings loaded from environment variables.
"""
import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

MCP_BINARY_PATH = BASE_DIR / "razorpay-mcp-server" / "razorpay-mcp-server.exe"

class Settings(BaseModel):
    PROJECT_NAME: str = "ReconAI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # MongoDB
    MONGO_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGO_DB: str = "recon_ai_db"

    # Razorpay
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TWtvyCy1XTG7Aj")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "365Vu5xQqH9R3Q3rqfl7b4zn")

    # MCP Server
    MCP_BINARY: str = str(MCP_BINARY_PATH)

    # Gemini API (for Q&A agent and fuzzy matching)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)

    # Recon Settings
    ROUNDING_TOLERANCE: float = 1.0  # Rs. 1.00 tolerance for rounding
    FUZZY_MATCH_CONFIDENCE_THRESHOLD: float = 0.85
    FUZZY_MATCH_REVIEW_THRESHOLD: float = 0.50
    GST_RATE: float = 0.18  # 18% GST on MDR

settings = Settings()
