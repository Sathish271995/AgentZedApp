import os, json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from utils.json_utils import safe_parse_json
load_dotenv()

KB_FILE = Path(__file__).parent.parent / "data" / "knowledge_base.json"

def _load(): 
    return json.loads(KB_FILE.read_text()) if KB_FILE.exists() else []

def _save(kb): 
    KB_FILE.parent.mkdir(exist_ok=True)
    KB_FILE.write_text(json.dumps(kb[-500:], indent=2))

def rag_knowledge_agent(pr_data: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    files   = pr_data.get("files_changed", [])
    kb      = _load()

    # Find similar PRs
    similar = []
    file_names = set(f.split("/")[-1] for f in files)
    for e in kb:
        overlap = file_names & set(f.split("/")[-1] for f in e.get("files",[]))
        if overlap:
            similar.append({**e, "overlap": list(overlap)})

    patterns, insight, decision = [], "No similar patterns found yet.", ""

    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            hist = "\n".join(f"- PR {s['pr_id']}: {s['title']} → {s['decision']}"
                             for s in similar[:3]) if similar else "None yet."
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":
                    f"RAG Knowledge Agent:\nPR: {pr_data['title']}\n"
                    f"Files: {', '.join(files)}\n"
                    f"Similar past PRs:\n{hist}\n"
                    f"Respond ONLY valid JSON:\n"
                    f'{{ "patterns":["pattern1","pattern2"], '
                    f'"historical_insight":"1-2 sentences", '
                    f'"decision_captured":"1 sentence" }}'}],
                temperature=0.2, max_tokens=400,
            )
            p = safe_parse_json(r.choices[0].message.content.strip())
            patterns = p.get("patterns", [])
            insight  = p.get("historical_insight", "")
            decision = p.get("decision_captured", "")

            kb.append({"pr_id":pr_data.get("pr_id"),
                       "title":pr_data.get("title"),
                       "files":files, "decision":decision,
                       "patterns":patterns})
            _save(kb)
        except Exception as e:
            patterns = [f"Pattern extraction failed: {e}"]

    return {
        "patterns":           patterns,
        "historical_insight": insight,
        "similar_prs":        similar[:3],
        "knowledge_base_size":len(kb),
        "agent":              "RAG Knowledge Agent",
    }
