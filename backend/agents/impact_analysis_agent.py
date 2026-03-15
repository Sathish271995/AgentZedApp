# import os, json
# from pathlib import Path
# from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()

# OWNERSHIP_FILE = Path(__file__).parent.parent / "data" / "team_ownership.json"

# def _load_ownership():
#     if OWNERSHIP_FILE.exists():
#         return json.loads(OWNERSHIP_FILE.read_text())
#     return {}

# KEYWORD_MAP = {
#     "payment":      ["Payments Team","QA Payments"],
#     "validator":    ["Platform Team"],
#     "utils":        ["Platform Team"],
#     "auth":         ["Security Team","Backend Team"],
#     "user":         ["Backend Team"],
#     "order":        ["Orders Team","QA Team"],
#     "notification": ["Platform Team"],
#     "database":     ["Platform Team","DBA Team"],
#     "migration":    ["DBA Team","Platform Team"],
#     "config":       ["DevOps Team"],
#     "deploy":       ["DevOps Team"],
#     "frontend":     ["Frontend Team"],
#     "api":          ["Backend Team"],
#     "router":       ["Backend Team"],
# }

# def impact_analysis_agent(pr_data: dict) -> dict:
#     api_key = os.getenv("OPENAI_API_KEY")
#     files   = pr_data.get("files_changed", [])

#     # Rule-based detection
#     teams = set()
#     for f in files:
#         fl = f.lower()
#         for kw, t in KEYWORD_MAP.items():
#             if kw in fl:
#                 teams.update(t)

#     if not teams: teams = {"Backend Team"}
#     teams_list = list(teams)
#     dep_risk   = "High" if len(teams)>=3 else "Medium" if len(teams)==2 else "Low"
#     signoff    = len(teams) >= 2

#     # LLM reasoning
#     reasoning = _reason(api_key, pr_data, teams_list)

#     return {
#         "impacted_teams":   teams_list,
#         "dependency_risk":  dep_risk,
#         "signoff_required": signoff,
#         "impact_reasoning": reasoning,
#         "confidence":       0.88,
#         "agent":            "Impact Analysis Agent",
#     }

# def _reason(api_key, pr_data, teams):
#     if not api_key: return f"Teams identified: {', '.join(teams)}"
#     try:
#         client = OpenAI(api_key=api_key)
#         r = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[{"role":"user","content":
#                 f"PR: {pr_data['title']}\nFiles: {', '.join(pr_data['files_changed'])}\n"
#                 f"Teams: {', '.join(teams)}\n"
#                 f"In 3 sentences, explain WHY each team is impacted and what they must do."}],
#             temperature=0.3, max_tokens=300,
#         )
#         return r.choices[0].message.content.strip()
#     except Exception as e:
#         return f"Teams: {', '.join(teams)}. AI error: {e}"




















import os, json
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

OWNERSHIP_FILE = Path(__file__).parent.parent / "data" / "team_ownership.json"

def _load_ownership():
    if OWNERSHIP_FILE.exists():
        return json.loads(OWNERSHIP_FILE.read_text())
    return {}

KEYWORD_MAP = {
    "payment":      ["Payments Team", "QA Payments"],
    "validator":    ["Platform Team"],
    "utils":        ["Platform Team"],
    "auth":         ["Security Team", "Backend Team"],
    "user":         ["Backend Team"],
    "order":        ["Orders Team", "QA Team"],
    "notification": ["Platform Team"],
    "database":     ["Platform Team", "DBA Team"],
    "migration":    ["DBA Team", "Platform Team"],
    "config":       ["DevOps Team"],
    "deploy":       ["DevOps Team"],
    "frontend":     ["Frontend Team"],
    "api":          ["Backend Team"],
    "router":       ["Backend Team"],
}


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


def impact_analysis_agent(pr_data: dict) -> dict:
    files = pr_data.get("files_changed", [])

    # Rule-based team detection using KEYWORD_MAP
    teams = set()
    for f in files:
        fl = f.lower()
        for kw, t in KEYWORD_MAP.items():
            if kw in fl:
                teams.update(t)

    if not teams:
        teams = {"Backend Team"}

    teams_list = list(teams)
    dep_risk   = "High" if len(teams) >= 3 else "Medium" if len(teams) == 2 else "Low"
    signoff    = len(teams) >= 2

    reasoning = _reason(pr_data, teams_list)

    return {
        "impacted_teams":   teams_list,
        "dependency_risk":  dep_risk,
        "signoff_required": signoff,
        "impact_reasoning": reasoning,
        "confidence":       0.88,
        "agent":            "Impact Analysis Agent",
    }


def _reason(pr_data: dict, teams: list) -> str:
    if not _is_configured():
        return f"Teams identified: {', '.join(teams)}"
    try:
        client = _get_client()
        r = client.chat.completions.create(
            model       = _deployment(),
            messages    = [{"role": "user", "content":
                f"PR: {pr_data['title']}\n"
                f"Files: {', '.join(pr_data['files_changed'])}\n"
                f"Teams: {', '.join(teams)}\n"
                f"In 3 sentences, explain WHY each team is impacted and what they must do."}],
            temperature = 0.3,
            max_tokens  = 300,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"Teams: {', '.join(teams)}. Azure AI error: {e}"