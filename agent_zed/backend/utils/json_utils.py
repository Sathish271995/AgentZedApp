import json
import re


def safe_parse_json(text: str) -> dict:
    """
    Robustly parse JSON from an LLM response that may contain markdown fences
    or extra surrounding text.

    Tries in order:
    1. Direct parse after stripping markdown fences
    2. Balanced-brace extraction (handles nested objects correctly)
    3. Greedy regex fallback
    """
    if not text:
        return {}

    # Strip markdown code fences: ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    # 1. Direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Balanced-brace extraction — walk forward finding matching closing brace
    start = cleaned.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(cleaned[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break   # malformed — fall through to regex

    # 3. Greedy regex last resort
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return {"error": "Invalid JSON", "raw": text}
