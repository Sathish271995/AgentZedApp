import json
import logging
from pathlib import Path

from utils.azure_client import get_azure_client, get_deployment
from utils.json_utils import safe_parse_json

logger = logging.getLogger("rag_agent")

KB_FILE = Path(__file__).parent.parent / "data" / "knowledge_base.json"
KB_MAX  = 500


def _load() -> list:
    try:
        if KB_FILE.exists():
            return json.loads(KB_FILE.read_text())
    except Exception as exc:
        logger.warning(f"Could not load knowledge base: {exc}")
    return []


def _save(kb: list) -> None:
    try:
        KB_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = KB_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(kb[-KB_MAX:], indent=2))
        tmp.replace(KB_FILE)
    except Exception as exc:
        logger.error(f"Could not save knowledge base: {exc}")


def rag_knowledge_agent(pr_data: dict) -> dict:
    client     = get_azure_client()
    deployment = get_deployment()
    files      = pr_data.get("files_changed", [])
    kb         = _load()

    # Find PRs that touched at least one of the same files (by basename)
    current_names = {f.split("/")[-1] for f in files}
    similar = []
    for entry in kb:
        overlap = current_names & {f.split("/")[-1] for f in entry.get("files", [])}
        if overlap:
            similar.append({**entry, "overlap": sorted(overlap)})

    patterns: list = []
    insight:  str  = "No similar patterns found yet."
    decision: str  = ""

    if client:
        try:
            file_list = "\n".join(f"  - {f}" for f in files) if files else "  (none)"
            hist = (
                "\n".join(
                    f"  - PR {s['pr_id']}: {s['title']} → {s['decision']}"
                    for s in similar[:3]
                )
                if similar else "None yet."
            )

            r = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content":
                    f"RAG Knowledge Agent — analyze this PR against historical patterns.\n\n"
                    f"Current PR: {pr_data['title']}\n"
                    f"Real changed files:\n{file_list}\n\n"
                    f"Similar past PRs that touched the same files:\n{hist}\n\n"
                    f"Respond ONLY with valid JSON (no markdown):\n"
                    f'{{"patterns": ["pattern observed in these files/PRs"], '
                    f'"historical_insight": "1-2 sentences about patterns seen", '
                    f'"decision_captured": "1 sentence summary of what this PR does"}}'}],
                temperature=0.2,
                max_tokens=400,
            )

            p        = safe_parse_json(r.choices[0].message.content.strip())
            patterns = p.get("patterns", [])
            insight  = p.get("historical_insight", "")
            decision = p.get("decision_captured", "")

            kb.append({
                "pr_id":    pr_data.get("pr_id"),
                "title":    pr_data.get("title"),
                "files":    files,
                "decision": decision,
                "patterns": patterns,
            })
            _save(kb)

        except Exception as exc:
            logger.error(f"rag_agent error: {exc}")
            patterns = [f"Pattern extraction failed: {exc}"]

    return {
        "patterns":            patterns,
        "historical_insight":  insight,
        "similar_prs":         similar[:3],
        "knowledge_base_size": len(kb),
        "agent":               "RAG Knowledge Agent",
    }
