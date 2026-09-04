"""
ReconAI Server Launcher
Launches FastAPI backend on port 8005 and React (Vite) frontend on port 5174 concurrently.
"""
import subprocess
import sys
import time
import os
from pathlib import Path

# Force UTF-8 on Windows stdout if possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

def main():
    print("=" * 65)
    print("  [ReconAI] Launching Settlement Reconciliation Engine...")
    print("  Razorpay AI Buildathon 2026 - Track 04: AI Finance Controller")
    print("=" * 65)
    
    # 1. Start FastAPI Backend (Uvicorn on Port 8005)
    print("[BACKEND] Starting FastAPI Backend at http://127.0.0.1:8005...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8005", "--reload"],
        cwd=str(BACKEND_DIR)
    )

    # 2. Start Vite Frontend (Port 5174)
    print("[FRONTEND] Starting React (Vite) Frontend at http://localhost:5174...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev", "--", "--host", "0.0.0.0"],
        cwd=str(FRONTEND_DIR)
    )

    print("\n" + "=" * 65)
    print("RECONAI PLATFORM OPERATIONAL:")
    print("   * React Dashboard: http://localhost:5174")
    print("   * FastAPI Backend & Docs: http://127.0.0.1:8005/docs")
    print("   * Webhook Ingestion URL: http://127.0.0.1:8005/api/recon/webhooks")
    print("   * Razorpay MCP Server: Connected via stdio & live API")
    print("=" * 65)
    print("Press Ctrl+C to terminate both servers.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down ReconAI servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
