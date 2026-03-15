import logging
import json
from pathlib import Path

from utils.azure_client import get_azure_client, get_deployment

logger = logging.getLogger("impact_analysis_agent")

OWNERSHIP_FILE = Path(__file__).parent.parent / "data" / "team_ownership.json"

KEYWORD_MAP = {
    "payment":      ["Payments Team", "QA Payments"],
    "billing":      ["Payments Team", "QA Payments"],
    "validator":    ["Platform Team"],
    "utils":        ["Platform Team"],
    "auth":         ["Security Team", "Backend Team"],
    "token":        ["Security Team", "Backend Team"],
    "user":         ["Backend Team"],
    "order":        ["Orders Team", "QA Team"],
    "notification": ["Platform Team"],
    "database":     ["Platform Team", "DBA Team"],
    "migration":    ["DBA Team", "Platform Team"],
    "config":       ["DevOps Team"],
    "deploy":       ["DevOps Team"],
    "dockerfile":   ["DevOps Team"],
    "frontend":     ["Frontend Team"],
    "component":    ["Frontend Team"],
    "api":          ["Backend Team"],
    "router":       ["Backend Team"],
    "middleware":   ["Backend Team", "Security Team"],
    "schema":       ["DBA Team"],
}


def _match_teams_for_file(filepath: str) -> set:
    teams: set = set()
    parts = filepath.lower().replace("\\", "/").split("/")
    full  = filepath.lower()
    for kw, kw_teams in KEYWORD_MAP.items():
        if any(kw in part for part in parts) or kw in full:
            teams.update(kw_teams)
    return teams


def impact_analysis_agent(pr_data: dict) -> dict:
    client     = get_azure_client()
    deployment = get_deployment()
    files      = pr_data.get("files_changed", [])

    # Rule-based team detection
    teams: set = set()
    for f in files:
        teams |= _match_teams_for_file(f)

    if not teams:
        teams = {"Backend Team"}

    teams_list = sorted(teams)
    dep_risk   = "High" if len(teams) >= 3 else "Medium" if len(teams) == 2 else "Low"
    signoff    = len(teams) >= 2

    reasoning = _reason(client, deployment, pr_data, teams_list)

    return {
        "impacted_teams":   teams_list,
        "dependency_risk":  dep_risk,
        "signoff_required": signoff,
        "impact_reasoning": reasoning,
        "confidence":       0.88,
        "agent":            "Impact Analysis Agent",
    }


def _reason(client, deployment: str, pr_data: dict, teams: list) -> str:
    if not client:
        return f"Teams identified: {', '.join(teams)}. Add Azure OpenAI credentials for AI reasoning."
    try:
        files     = pr_data.get("files_changed", [])
        file_list = "\n".join(f"  - {f}" for f in files) if files else "  (none)"
        r = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content":
                f"PR: {pr_data['title']}\n"
                f"Real changed files:\n{file_list}\n"
                f"Impacted teams: {', '.join(teams)}\n\n"
                f"In 3 sentences, explain WHY each team is impacted based on "
                f"the specific files changed, and what action each team must take."}],
            temperature=0.3,
            max_tokens=350,
        )
        return r.choices[0].message.content.strip()
    except Exception as exc:
        logger.error(f"impact reasoning error: {exc}")
        return f"Teams: {', '.join(teams)}. AI reasoning unavailable: {exc}"
