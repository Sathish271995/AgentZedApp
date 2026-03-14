import os
from openai import OpenAI
from dotenv import load_dotenv
from utils.json_utils import safe_parse_json
load_dotenv()

def pr_review_agent(pr_data: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback("OPENAI_API_KEY not set")

    files = pr_data.get("files_changed", [])
    client = OpenAI(api_key=api_key)

    prompt = f"""You are a senior technical lead — PR First Responder Agent.

PR Title: {pr_data['title']}
Files Changed: {', '.join(files)}
Repository: {pr_data.get('repo','N/A')}
Branch: {pr_data.get('head_branch','')} → {pr_data.get('base_branch','main')}
Description: {(pr_data.get('body','') or 'None')[:300]}

Respond ONLY with valid JSON (no markdown):
{{
  "summary": "2-3 sentence technical summary",
  "risk_level": "High | Medium | Low",
  "cosmetic_issues": ["issue1","issue2"],
  "missing_tests": ["test1","test2"],
  "missing_docs": ["doc1"],
  "merge_conflicts": true | false,
  "merge_conflict_files": ["file1"],
  "approval_recommendation": "Approve | Request Changes | Needs Discussion",
  "approval_reasoning": "1-2 sentences"
}}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.2, max_tokens=700,
        )
        p = safe_parse_json(resp.choices[0].message.content.strip())
        return {
            "summary":                p.get("summary",""),
            "risk_level":             p.get("risk_level","Medium"),
            "cosmetic_issues":        p.get("cosmetic_issues",[]),
            "missing_tests":          p.get("missing_tests",[]),
            "missing_docs":           p.get("missing_docs",[]),
            "merge_conflicts":        bool(p.get("merge_conflicts",False)),
            "merge_conflict_files":   p.get("merge_conflict_files",[]),
            "approval_recommendation":p.get("approval_recommendation","Request Changes"),
            "approval_reasoning":     p.get("approval_reasoning",""),
            "confidence":             0.92,
            "agent":                  "PR First Responder Agent",
        }
    except Exception as e:
        return _fallback(str(e))

def _fallback(reason):
    return {"summary":f"Review unavailable: {reason}","risk_level":"Unknown",
            "cosmetic_issues":[],"missing_tests":[],"missing_docs":[],
            "merge_conflicts":False,"merge_conflict_files":[],
            "approval_recommendation":"Needs Discussion","approval_reasoning":reason,
            "confidence":0.0,"agent":"PR First Responder Agent"}
