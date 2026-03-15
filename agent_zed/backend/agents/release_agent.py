import json
import logging
from pathlib import Path

from utils.azure_client import get_azure_client, get_deployment

logger = logging.getLogger("release_agent")

CALENDAR_FILE = Path(__file__).parent.parent / "data" / "release_calendar.json"


def _load_calendar() -> dict:
    if CALENDAR_FILE.exists():
        return json.loads(CALENDAR_FILE.read_text())
    return {"upcoming_releases": [], "freeze_windows": []}


def _file_tokens(files: list) -> set:
    tokens: set = set()
    for f in files:
        for part in f.lower().replace("\\", "/").split("/"):
            for seg in part.replace("_", " ").replace(".", " ").split():
                tokens.add(seg)
    return tokens


def release_agent(pr_data: dict) -> dict:
    client     = get_azure_client()
    deployment = get_deployment()
    files      = pr_data.get("files_changed", [])
    tokens     = _file_tokens(files)
    cal        = _load_calendar()

    # Conflict detection
    conflicts, conflict_dates = [], []
    for rel in cal.get("upcoming_releases", []):
        for svc in rel.get("services", []):
            svc_tokens = set(svc.lower().replace("_", " ").split())
            if svc_tokens & tokens:
                if rel["date"] not in conflict_dates:
                    conflict_dates.append(rel["date"])
                    conflicts.append(rel)

    # Stakeholders
    stakeholders: set = {"Release Manager"}
    if tokens & {"payment", "payments", "billing"}:
        stakeholders.update(["Payments Team", "QA Lead"])
    if tokens & {"auth", "security", "token", "middleware"}:
        stakeholders.update(["Security Team", "QA Lead"])
    if tokens & {"database", "migration", "schema", "db"}:
        stakeholders.add("DBA Team")
    for c in conflicts:
        stakeholders.add(c.get("owner", "Release Manager"))

    if tokens & {"payment", "payments", "billing"}:
        precaution = "🚀 Run full regression — payment-critical files changed"
    elif conflicts:
        precaution = f"⚠️ Coordinate with Release Manager — conflicts on {', '.join(conflict_dates)}"
    else:
        precaution = "✅ Standard tests sufficient — no immediate conflicts"

    reasoning = _reason(client, deployment, pr_data, bool(conflicts), conflicts, list(stakeholders))

    return {
        "release_conflict":          bool(conflicts),
        "conflicting_release_dates": conflict_dates,
        "conflicting_releases":      conflicts,
        "suggested_stakeholders":    sorted(stakeholders),
        "precaution":                precaution,
        "release_reasoning":         reasoning,
        "confidence":                0.85,
        "agent":                     "Release Intelligence Agent",
    }


def _reason(client, deployment: str, pr_data: dict, has_conflict: bool, conflicts: list, stakeholders: list) -> str:
    if not client:
        return "Release check complete. Add Azure OpenAI credentials for AI reasoning."
    try:
        files     = pr_data.get("files_changed", [])
        file_list = "\n".join(f"  - {f}" for f in files) if files else "  (none)"
        ctx = (
            f"Conflicts with upcoming releases: {[c['description'] for c in conflicts]}"
            if has_conflict else "No release conflicts found."
        )
        r = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content":
                f"Release Manager review:\n"
                f"PR: {pr_data['title']}\n"
                f"Real changed files:\n{file_list}\n"
                f"{ctx}\n"
                f"Stakeholders to notify: {', '.join(stakeholders)}\n\n"
                f"In 3 sentences: describe the release risks introduced by these specific "
                f"files and the required actions before this can go to production."}],
            temperature=0.3,
            max_tokens=350,
        )
        return r.choices[0].message.content.strip()
    except Exception as exc:
        logger.error(f"release reasoning error: {exc}")
        return f"Release check done. AI reasoning unavailable: {exc}"
