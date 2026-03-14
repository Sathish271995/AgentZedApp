"""
Agent Zed Router
================
POST /webhook/github                        → GitHub fires this on PR approve/merge
POST /run-agent-zed                         → Manual trigger
GET  /api/pr-analyses                       → List all analyses
GET  /api/pr-analyses/{id}                  → Get one
DELETE /api/pr-analyses/{id}               → Delete
POST /api/pr-analyses/{id}/rerun           → Re-run all 4 agents
GET  /api/pr-analyses/{id}/comments        → List comments
POST /api/pr-analyses/{id}/comments        → Add comment (Agent Zed auto-replies)
PUT  /api/pr-analyses/{id}/comments/{cid}  → Edit comment
DELETE /api/pr-analyses/{id}/comments/{cid}→ Delete comment
GET  /api/stats                             → Dashboard statistics
"""

from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
import hashlib, hmac, json, os
from dotenv import load_dotenv

from database import (
    save_pr_analysis, get_all_pr_analyses, get_pr_by_id,
    delete_pr_analysis, get_stats,
    create_pr_comment, get_pr_comments, update_pr_comment, delete_pr_comment
)
from agents.pr_review_agent       import pr_review_agent
from agents.impact_analysis_agent import impact_analysis_agent
from agents.release_agent         import release_agent
from agents.rag_agent             import rag_knowledge_agent
from notifications                import send_team_notifications

load_dotenv()
router = APIRouter()

# ── Pydantic Models ───────────────────────────────────────────────────────────
class PRRequest(BaseModel):
    pr_id:         str
    title:         str
    files_changed: List[str]
    author:        Optional[str] = "manual"
    repo:          Optional[str] = ""
    pr_url:        Optional[str] = ""
    event_type:    Optional[str] = "manual"
    reviewer:      Optional[str] = ""
    base_branch:   Optional[str] = "main"
    head_branch:   Optional[str] = ""
    body:          Optional[str] = ""

    class Config:
        json_schema_extra = {"example": {
            "pr_id": "PR-120", "title": "Add payment CRUD API",
            "files_changed": ["routers/payments.py", "database.py"],
            "author": "Sathish271995", "repo": "Sathish271995/AgentZed",
            "event_type": "approved", "base_branch": "main", "head_branch": "feature/payment-crud"
        }}

class CommentCreate(BaseModel):
    author:       str
    comment:      str
    comment_type: Optional[str] = "general"
    file_ref:     Optional[str] = ""

    class Config:
        json_schema_extra = {"example": {
            "author": "Sathish271995",
            "comment": "This validation doesn't handle null payment methods",
            "comment_type": "bug", "file_ref": "routers/payments.py:45"
        }}

class CommentUpdate(BaseModel):
    comment: str

# ── GitHub Webhook ────────────────────────────────────────────────────────────
def _verify(payload: bytes, sig: str) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret: return True
    exp = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(exp, sig or "")

@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_github_event:      str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    payload = await request.body()
    if not _verify(payload, x_hub_signature_256 or ""):
        raise HTTPException(403, "Invalid signature")

    data   = json.loads(payload)
    action = data.get("action","")
    pr     = data.get("pull_request",{})

    is_approved = (x_github_event=="pull_request_review"
                   and data.get("review",{}).get("state")=="approved")
    is_merged   = (x_github_event=="pull_request"
                   and action=="closed" and pr.get("merged",False))
    is_opened   = (x_github_event=="pull_request" and action=="opened")

    if not (is_approved or is_merged or is_opened):
        return {"status":"ignored","event":x_github_event,"action":action}

    files = _extract_files(data)
    pr_data = {
        "pr_id":        str(pr.get("number","unknown")),
        "title":        pr.get("title","Untitled PR"),
        "files_changed": files,
        "author":       pr.get("user",{}).get("login","unknown"),
        "repo":         data.get("repository",{}).get("full_name",""),
        "pr_url":       pr.get("html_url",""),
        "event_type":   "approved" if is_approved else ("merged" if is_merged else "opened"),
        "reviewer":     data.get("review",{}).get("user",{}).get("login","") if is_approved else "",
        "base_branch":  pr.get("base",{}).get("ref","main"),
        "head_branch":  pr.get("head",{}).get("ref",""),
        "body":         pr.get("body","") or "",
    }
    print(f"\n🔔 GitHub event: {x_github_event} / {action} on PR#{pr_data['pr_id']}")
    return await _pipeline(pr_data)

def _extract_files(data):
    files = data.get("files",[])
    if files: return [f.get("filename","") for f in files]
    title = data.get("pull_request",{}).get("title","").lower()
    if "payment" in title: return ["routers/payments.py","database.py"]
    if "auth"    in title: return ["auth_service.py","middleware/auth.py"]
    return ["app/main.py"]

# ── Manual Trigger ────────────────────────────────────────────────────────────
@router.post("/run-agent-zed")
async def run_manual(body: PRRequest):
    data = body.dict()
    return await _pipeline(data)

# ── PR Analyses CRUD ──────────────────────────────────────────────────────────
@router.get("/api/pr-analyses")
def list_analyses():
    return get_all_pr_analyses()

@router.get("/api/pr-analyses/{db_id}")
def get_analysis(db_id: int):
    r = get_pr_by_id(db_id)
    if not r: raise HTTPException(404,"Not found")
    return r

@router.delete("/api/pr-analyses/{db_id}")
def del_analysis(db_id: int):
    if not delete_pr_analysis(db_id): raise HTTPException(404,"Not found")
    return {"message":f"PR analysis {db_id} deleted"}

@router.post("/api/pr-analyses/{db_id}/rerun")
async def rerun(db_id: int):
    pr = get_pr_by_id(db_id)
    if not pr: raise HTTPException(404,"Not found")
    return await _pipeline({
        "pr_id":pr["pr_id"],"title":pr["title"],
        "files_changed":pr["files_changed"],
        "author":pr.get("author",""),"repo":pr.get("repo",""),
        "pr_url":pr.get("pr_url",""),"event_type":"rerun",
        "reviewer":"","base_branch":pr.get("base_branch","main"),
        "head_branch":pr.get("head_branch",""),"body":"",
    })

@router.get("/api/stats")
def stats():
    return get_stats()

# ── Comments CRUD ─────────────────────────────────────────────────────────────
@router.get("/api/pr-analyses/{db_id}/comments")
def list_comments(db_id: int):
    return get_pr_comments(db_id)

@router.post("/api/pr-analyses/{db_id}/comments")
def add_comment(db_id: int, body: CommentCreate):
    pr = get_pr_by_id(db_id)
    if not pr: raise HTTPException(404,"PR not found")
    ai = _ai_reply(body.comment, pr)
    cid = create_pr_comment(db_id, body.author, body.comment,
                             body.comment_type, body.file_ref or "", ai)
    return {"id":cid,"author":body.author,"comment":body.comment,
            "comment_type":body.comment_type,"file_ref":body.file_ref,
            "ai_response":ai,"message":"Comment added — Agent Zed responded"}

@router.put("/api/pr-analyses/{db_id}/comments/{cid}")
def edit_comment(db_id:int, cid:int, body:CommentUpdate):
    if not update_pr_comment(cid, body.comment): raise HTTPException(404,"Not found")
    return {"message":"Updated","id":cid}

@router.delete("/api/pr-analyses/{db_id}/comments/{cid}")
def del_comment(db_id:int, cid:int):
    if not delete_pr_comment(cid): raise HTTPException(404,"Not found")
    return {"message":"Deleted"}

# ── Pipeline ──────────────────────────────────────────────────────────────────
async def _pipeline(pr_data: dict):
    print(f"  🕵️  PR First Responder running...")
    rv = pr_review_agent(pr_data)

    print(f"  🎯  Impact Analysis running...")
    ia = impact_analysis_agent(pr_data)

    print(f"  🚀  Release Intelligence running...")
    ri = release_agent(pr_data)

    print(f"  🧠  RAG Knowledge running...")
    rg = rag_knowledge_agent(pr_data)

    result = {**pr_data,
              "PR Review":rv, "Impact Analysis":ia,
              "Release Intelligence":ri, "RAG Knowledge":rg}

    db_id = save_pr_analysis(result)
    result["db_id"] = db_id
    print(f"  ✅  Saved to PostgreSQL id={db_id}")

    notified = send_team_notifications(result)
    result["notifications_sent"] = notified
    return result

def _ai_reply(comment:str, pr:dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return "Agent Zed: Add OPENAI_API_KEY for AI responses."
    try:
        from openai import OpenAI
        c = OpenAI(api_key=api_key)
        r = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":
                f"You are Agent Zed, a senior AI code reviewer.\n"
                f"PR #{pr['pr_id']}: {pr['title']}\n"
                f"Files: {', '.join(pr.get('files_changed',[]))}\n"
                f"Developer comment: \"{comment}\"\n"
                f"Reply as a helpful senior engineer in 2-3 sentences."}],
            temperature=0.3, max_tokens=200,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Agent Zed: {str(e)}"
