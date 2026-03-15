# import os, json
# from pathlib import Path
# from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()

# CALENDAR_FILE = Path(__file__).parent.parent / "data" / "release_calendar.json"

# def _load_calendar():
#     if CALENDAR_FILE.exists():
#         return json.loads(CALENDAR_FILE.read_text())
#     return {"upcoming_releases":[], "freeze_windows":[]}

# def release_agent(pr_data: dict) -> dict:
#     api_key = os.getenv("OPENAI_API_KEY")
#     files   = pr_data.get("files_changed", [])
#     fl      = " ".join(files).lower()
#     cal     = _load_calendar()

#     # Conflict detection
#     conflicts, conflict_dates = [], []
#     for rel in cal.get("upcoming_releases", []):
#         for svc in rel.get("services", []):
#             if svc.replace("_","") in fl.replace("_","").replace("/",""):
#                 if rel["date"] not in conflict_dates:
#                     conflict_dates.append(rel["date"])
#                     conflicts.append(rel)

#     # Stakeholders
#     stakeholders = {"Release Manager"}
#     if any(p in fl for p in ["payment","billing"]): stakeholders.update(["Payments Team","QA Lead"])
#     if any(p in fl for p in ["auth","security"]):   stakeholders.update(["Security Team","QA Lead"])
#     if any(p in fl for p in ["database","migration"]): stakeholders.add("DBA Team")
#     for c in conflicts: stakeholders.add(c.get("owner","Release Manager"))

#     precaution = (
#         "🚀 Run full regression — payment-critical files changed"
#         if "payment" in fl else
#         f"⚠️ Coordinate with Release Manager — conflicts on {', '.join(conflict_dates)}"
#         if conflicts else
#         "✅ Standard tests sufficient — no immediate conflicts"
#     )

#     reasoning = _reason(api_key, pr_data, bool(conflicts), conflicts, list(stakeholders))

#     return {
#         "release_conflict":          bool(conflicts),
#         "conflicting_release_dates": conflict_dates,
#         "conflicting_releases":      conflicts,
#         "suggested_stakeholders":    list(stakeholders),
#         "precaution":                precaution,
#         "release_reasoning":         reasoning,
#         "confidence":                0.85,
#         "agent":                     "Release Intelligence Agent",
#     }

# def _reason(api_key, pr_data, has_conflict, conflicts, stakeholders):
#     if not api_key: return "Release check complete. Add OPENAI_API_KEY for AI reasoning."
#     try:
#         client = OpenAI(api_key=api_key)
#         ctx = f"Conflicts: {[c['description'] for c in conflicts]}" if has_conflict else "No conflicts."
#         r = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role":"user","content":
#                 f"Release Manager review:\nPR: {pr_data['title']}\n"
#                 f"Files: {', '.join(pr_data['files_changed'])}\n{ctx}\n"
#                 f"Stakeholders: {', '.join(stakeholders)}\n"
#                 f"In 3 sentences: release risks + required actions before production."}],
#             temperature=0.3, max_tokens=300,
#         )
#         return r.choices[0].message.content.strip()
#     except Exception as e:
#         return f"Release check done. AI error: {e}"






import os, json
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

CALENDAR_FILE = Path(__file__).parent.parent / "data" / "release_calendar.json"


def _load_calendar():
    if CALENDAR_FILE.exists():
        return json.loads(CALENDAR_FILE.read_text())
    return {"upcoming_releases": [], "freeze_windows": []}

def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key        = os.getenv("AZURE_OPENAI_KEY"),
        api_version    = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )

def _deployment() -> str:
    return os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt4v")

def _is_configured() -> bool:
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_KEY"))


def release_agent(pr_data: dict) -> dict:
    files = pr_data.get("files_changed", [])
    fl    = " ".join(files).lower()
    cal   = _load_calendar()

    # Release conflict detection
    conflicts, conflict_dates = [], []
    for rel in cal.get("upcoming_releases", []):
        for svc in rel.get("services", []):
            if svc.replace("_", "") in fl.replace("_", "").replace("/", ""):
                if rel["date"] not in conflict_dates:
                    conflict_dates.append(rel["date"])
                    conflicts.append(rel)

    # Stakeholders
    stakeholders = {"Release Manager"}
    if any(p in fl for p in ["payment", "billing"]):
        stakeholders.update(["Payments Team", "QA Lead"])
    if any(p in fl for p in ["auth", "security"]):
        stakeholders.update(["Security Team", "QA Lead"])
    if any(p in fl for p in ["database", "migration"]):
        stakeholders.add("DBA Team")
    for c in conflicts:
        stakeholders.add(c.get("owner", "Release Manager"))

    precaution = (
        "Run full regression — payment-critical files changed"
        if "payment" in fl else
        f"Coordinate with Release Manager — conflicts on {', '.join(conflict_dates)}"
        if conflicts else
        "Standard tests sufficient — no immediate conflicts"
    )

    reasoning = _reason(pr_data, bool(conflicts), conflicts, list(stakeholders))

    return {
        "release_conflict":          bool(conflicts),
        "conflicting_release_dates": conflict_dates,
        "conflicting_releases":      conflicts,
        "suggested_stakeholders":    list(stakeholders),
        "precaution":                precaution,
        "release_reasoning":         reasoning,
        "confidence":                0.85,
        "agent":                     "Release Intelligence Agent",
    }


def _reason(pr_data: dict, has_conflict: bool, conflicts: list, stakeholders: list) -> str:
    if not _is_configured():
        return "Release check complete. Configure Azure OpenAI for AI reasoning."
    try:
        client = _get_client()
        ctx    = f"Conflicts: {[c['description'] for c in conflicts]}" if has_conflict else "No conflicts."
        r = client.chat.completions.create(
            model       = _deployment(),
            messages    = [{"role": "user", "content":
                f"Release Manager review:\n"
                f"PR: {pr_data['title']}\n"
                f"Files: {', '.join(pr_data['files_changed'])}\n"
                f"{ctx}\n"
                f"Stakeholders: {', '.join(stakeholders)}\n"
                f"In 3 sentences: release risks + required actions before production."}],
            temperature = 0.3,
            max_tokens  = 300,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Release check done. Azure AI error: {e}"