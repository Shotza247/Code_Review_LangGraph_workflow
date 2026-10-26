import json
from datetime import datetime, timezone
from typing import Any, Callable

from .outputs import save_json

MAX_PREVIEW = 80


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _summarize(value: Any) -> dict[str, Any]:
    if value is None:
        return {"type": "none"}
    if isinstance(value, str):
        return {
            "type": "str",
            "chars": len(value),
            "preview": value.replace("\n", " ")[:MAX_PREVIEW],
        }
    if isinstance(value, list):
        return {
            "type": "list",
            "len": len(value),
            "sample": value[:3],
        }
    if isinstance(value, dict):
        summary: dict[str, Any] = {
            "type": "dict",
            "keys": sorted(str(k) for k in value.keys())[:12],
            "key_count": len(value),
        }
        if "score" in value:
            summary["score"] = value.get("score")
        if "status" in value:
            summary["status"] = value.get("status")
        if "findings" in value and isinstance(value["findings"], list):
            summary["findings"] = len(value["findings"])
        if "missing" in value and isinstance(value["missing"], list):
            summary["missing"] = len(value["missing"])
        return summary
    return {"type": type(value).__name__, "value": repr(value)[:MAX_PREVIEW]}


def _emit(event: dict[str, Any]) -> None:
    print("AUDIT " + json.dumps(event, ensure_ascii=False, sort_keys=True))


def _persist(state: dict[str, Any], audit_log: list[dict[str, Any]]) -> None:
    out = state.get("output_dir")
    if out:
        save_json(out, "audit_log.json", audit_log)


def make_node_audit_event(node: str, before: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    changed_keys = sorted(k for k in update.keys() if k != "audit_log")
    merged = {**before, **update}
    return {
        "event": "node_executed",
        "timestamp": _now(),
        "node": node,
        "changed_keys": changed_keys,
        "before": {key: _summarize(before.get(key)) for key in changed_keys},
        "after": {key: _summarize(merged.get(key)) for key in changed_keys},
    }


def audit_node(node: str, func: Callable[[dict[str, Any]], dict[str, Any]]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def wrapped(state: dict[str, Any]) -> dict[str, Any]:
        update = func(state) or {}
        event = make_node_audit_event(node, state, update)
        audit_log = list(state.get("audit_log", [])) + [event]
        update["audit_log"] = audit_log
        _emit(event)
        _persist({**state, **update}, audit_log)
        return update

    return wrapped


def audit_decision(state: dict[str, Any], decision: str, reason: str) -> None:
    event = {
        "event": "route_decision",
        "timestamp": _now(),
        "node": "diagrams",
        "decision": decision,
        "reason": reason,
    }
    audit_log = list(state.get("audit_log", [])) + [event]
    _emit(event)
    _persist(state, audit_log)
