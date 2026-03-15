import json, re

def safe_parse_json(text: str) -> dict:
    if not text: return {}
    cleaned = re.sub(r"^```(?:json)?\s*","",text.strip())
    cleaned = re.sub(r"\s*```$","",cleaned.strip())
    try: return json.loads(cleaned)
    except Exception:
        m = re.search(r"\{.*\}",cleaned,re.DOTALL)
        if m:
            try: return json.loads(m.group())
            except: pass
    return {"error":"Invalid JSON","raw":text}
