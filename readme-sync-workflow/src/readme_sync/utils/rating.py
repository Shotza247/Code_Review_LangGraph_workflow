from .json_utils import extract_json
from .prompts import SYSTEM


def format_rubric(rubric: dict) -> str:
    return "\n".join(f"- {c['id']} (max {c['weight']}): {c['description']}" for c in rubric["criteria"])


def llm_json(llm, prompt: str) -> dict:
    """Call the LLM and parse JSON, with one repair retry."""
    raw = llm.generate(prompt, system=SYSTEM)
    try:
        return extract_json(raw)
    except ValueError as exc:
        retry = (
            prompt
            + "\n\nYour previous reply was not valid JSON. Reply with ONLY minified valid JSON, "
            + "no prose, no fences, no trailing commas. Preserve the same schema.\n\n"
            + f"JSON parse error: {exc}\n\nInvalid reply excerpt:\n<<<\n{raw[:3000]}\n>>>"
        )
        try:
            return extract_json(llm.generate(retry, system=SYSTEM))
        except ValueError as retry_exc:
            raise ValueError(f"Model did not return valid JSON after repair retry: {retry_exc}") from retry_exc


def normalize_rating(rating: dict, rubric: dict) -> dict:
    """Recompute totals in code so arithmetic never depends on the model."""
    got = rating.get("criteria", {})
    if isinstance(got, list):  # model returned [{"id": ..., "score": ...}]
        got = {item.get("id"): item for item in got if isinstance(item, dict)}
    criteria, total = {}, 0.0
    for c in rubric["criteria"]:
        entry = got.get(c["id"], {})
        if not isinstance(entry, dict):  # model returned a bare number/string, e.g. "install": 12
            entry = {"score": entry}
        try:
            score = float(entry.get("score", 0))
        except (TypeError, ValueError):
            score = 0.0
        score = max(0.0, min(score, c["weight"]))
        criteria[c["id"]] = {"score": score, "max": c["weight"], "note": entry.get("note", "")}
        total += score
    rating["criteria"] = criteria
    rating["score"] = round(total)
    return rating
