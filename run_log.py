"""
Structured run log for FitFindr (capstone).

Every call to agent.run_agent() appends one JSON record to logs/runs.jsonl,
including runs that crash. Read it back with:

    python run_log.py            the last 10 records, one line each
    python run_log.py -n 25      the last 25
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

LOG_PATH = config.ROOT / "logs" / "runs.jsonl"


def write(record: dict) -> None:
    """Append one record. Logging must never break a run, so errors are swallowed."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def build_record(query, wardrobe, session, error, started, duration_s,
                 calls, tokens) -> dict:
    """One record with named fields: what came in, what came out, how long."""
    session = session or {}
    parsed = session.get("parsed") or {}
    item = session.get("selected_item") or {}
    if error is not None:
        outcome = "crashed"
    elif session.get("error"):
        outcome = "stopped"
    else:
        outcome = "fit_card"
    return {
        "timestamp": started.isoformat(timespec="seconds"),
        "query": query,
        "wardrobe_items": len((wardrobe or {}).get("items") or []),
        "description": parsed.get("description"),
        "size": parsed.get("size"),
        "max_price": parsed.get("max_price"),
        "rewrite_tried": session.get("rewrite_tried", False),
        "rewritten_description": session.get("rewritten_description"),
        "results": len(session.get("search_results") or []),
        "selected_item": item.get("id"),
        "selected_title": item.get("title"),
        "outcome": outcome,
        "message": session.get("error"),
        "error": error,
        "duration_s": round(duration_s, 3),
        "model_calls": calls,
        "prompt_tokens": tokens["prompt"],
        "output_tokens": tokens["output"],
    }


def now() -> datetime:
    return datetime.now(timezone.utc)


def read(n: int = 10) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    return [json.loads(line) for line in lines[-n:]]


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("-n") + 1]) if "-n" in sys.argv else 10
    for r in read(n):
        print(json.dumps(r, ensure_ascii=False))