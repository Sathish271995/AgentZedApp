"""
Agent Zed – Full Application
============================
Payment CRUD API  +  GitHub Webhook  +  4 AI Agents  +  PostgreSQL

Endpoints:
  Payment CRUD  →  /api/payments
  Agent Zed     →  /webhook/github  |  /run-agent-zed
  Dashboard     →  /api/pr-analyses
"""

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import hashlib, hmac, json, os
from dotenv import load_dotenv

from database import init_db
from routers  import payments, agent_zed

load_dotenv()

app = FastAPI(title="Agent Zed – Payment Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Agent Zed started — all tables ready.")

@app.get("/")
def root():
    return {
        "app":      "Agent Zed – Payment Intelligence",
        "payment_crud": "/api/payments",
        "webhook":      "/webhook/github",
        "dashboard":    "/api/pr-analyses",
        "docs":         "/docs"
    }

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(payments.router,   prefix="/api/payments",    tags=["Payment CRUD"])
app.include_router(agent_zed.router,                              tags=["Agent Zed"])
