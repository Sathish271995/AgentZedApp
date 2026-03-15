import logging

from utils.azure_client import get_azure_client, get_deployment
from utils.json_utils import safe_parse_json

logger = logging.getLogger("pr_review_agent")


def pr_review_agent(pr_data: dict) -> dict:
    client     = get_azure_client()
    deployment = get_deployment()

    if not client:
        return _fallback("Azure OpenAI credentials not configured")

    files     = pr_data.get("files_changed", [])
    file_list = "\n".join(f"  - {f}" for f in files) if files else "  (none)"

    prompt = f"""You are a senior technical lead acting as a PR First Responder Agent.

PR Title: {pr_data['title']}
Repository: {pr_data.get('repo', 'N/A')}
Branch: {pr_data.get('head_branch', '')} → {pr_data.get('base_branch', 'main')}
Author: {pr_data.get('author', 'unknown')}
Description: {(pr_data.get('body', '') or 'None')[:400]}

Files Changed ({len(files)} total):
{file_list}

Analyze these ACTUAL changed files carefully. Consider:
- What modules/layers are touched (API, DB, auth, payments, etc.)
- Whether tests and docs are likely missing based on file names
- Potential merge conflict risk based on file count and type
- Overall risk level based on what was changed

Respond ONLY with valid JSON (no markdown fences):
{{
  "summary": "2-3 sentence technical summary of what this PR actually changes",
  "risk_level": "High | Medium | Low",
  "cosmetic_issues": ["specific issue based on real files"],
  "missing_tests": ["specific test file that should exist for these files"],
  "missing_docs": ["specific doc that should be updated"],
  "merge_conflicts": true | false,
  "merge_conflict_files": ["file most likely to have conflicts"],
  "approval_recommendation": "Approve | Request Changes | Needs Discussion",
  "approval_reasoning": "1-2 sentences specific to these files"
}}"""

    try:
        resp = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
        )
        raw = resp.choices[0].message.content.strip()
        p   = safe_parse_json(raw)

        filled     = sum(1 for k in ["summary", "risk_level", "approval_recommendation", "approval_reasoning"] if p.get(k))
        confidence = round(0.6 + (filled / 4) * 0.35, 2)

        return {
            "summary":                 p.get("summary", ""),
            "risk_level":              p.get("risk_level", "Medium"),
            "cosmetic_issues":         p.get("cosmetic_issues", []),
            "missing_tests":           p.get("missing_tests", []),
            "missing_docs":            p.get("missing_docs", []),
            "merge_conflicts":         bool(p.get("merge_conflicts", False)),
            "merge_conflict_files":    p.get("merge_conflict_files", []),
            "approval_recommendation": p.get("approval_recommendation", "Request Changes"),
            "approval_reasoning":      p.get("approval_reasoning", ""),
            "confidence":              confidence,
            "agent":                   "PR First Responder Agent",
        }
    except Exception as exc:
        logger.error(f"pr_review_agent error: {exc}")
        return _fallback(str(exc))


def _fallback(reason: str) -> dict:
    return {
        "summary":                 f"Review unavailable: {reason}",
        "risk_level":              "Unknown",
        "cosmetic_issues":         [],
        "missing_tests":           [],
        "missing_docs":            [],
        "merge_conflicts":         False,
        "merge_conflict_files":    [],
        "approval_recommendation": "Needs Discussion",
        "approval_reasoning":      reason,
        "confidence":              0.0,
        "agent":                   "PR First Responder Agent",
    }
