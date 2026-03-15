"""
Agent Zed – Full Application
============================
Payment CRUD API  +  GitHub Webhook  +  4 AI Agents  +  PostgreSQL

Endpoints:
  Payment CRUD  →  /api/payments
  Agent Zed     →  /webhook/github  |  /run-agent-zed
  Dashboard     →  /api/pr-analyses
  Stats         →  /api/stats
"""

import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers  import payments, agent_zed

load_dotenv()

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Agent Zed – Payment Intelligence",
    version="1.0.0",
    description="GitHub PR analysis with 4 AI agents + Payment CRUD",
)

# ── CORS — restrict in production via ALLOWED_ORIGINS env var ────────────────
import os
_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    logging.getLogger("main").info("✅ Agent Zed started — all tables ready.")


@app.get("/", tags=["Health"])
def root():
    return {
        "app":           "Agent Zed – Payment Intelligence",
        "payment_crud":  "/api/payments",
        "webhook":       "/webhook/github",
        "manual_run":    "/run-agent-zed",
        "dashboard":     "/api/pr-analyses",
        "stats":         "/api/stats",
        "docs":          "/docs",
    }


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(payments.router,  prefix="/api/payments", tags=["Payment CRUD"])
app.include_router(agent_zed.router,                         tags=["Agent Zed"])
