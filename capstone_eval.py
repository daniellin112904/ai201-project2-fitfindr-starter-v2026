"""
Capstone test: runs the five criteria in criteria.md once (one trial).

Run it three separate times, then summarise:

    python capstone_eval.py --label before --trial 1
    python capstone_eval.py --label before --trial 2
    python capstone_eval.py --label before --trial 3
    python capstone_eval.py --label before --summary

Each trial is its own process, so the session request budget in config.py
starts fresh each time. The cache is off for every run. Each trial is saved
to results/capstone_<label>_trial<N>.json; the summary writes
results/capstone_<label>.md.
"""

import argparse
import contextlib
import io
import json
from datetime import datetime

import config
import run_log
import trace as trace_module
from agent import run_agent
from utils.data_loader import get_example_wardrobe

# Fixed before any results, from criteria.md.
FIXABLE = {
    "comfy sweater": {"lst_008", "lst_012", "lst_027", "lst_030"},
    "purse": {"lst_039"},
    "running shoes": {"lst_019", "lst_035"},
    "button up shirt": {"lst_029", "lst_003"},
    "ankle booties": {"lst_028"},
}
MATCHING = [
    "vintage graphic tee under $30",
    "denim jacket under $50",
    "90s track jacket in size M",
    "platform sneakers size 8",
    "silk slip dress in midi length under $40",
]
IMPOSSIBLE = [
    "designer ballgown size XXS under $5",
    "tuxedo under $5",
    "winter coat size XXS under $5",
    "swimsuit under $5",
    "ski goggles under $5",
]
LOG_FIELDS = ["timestamp", "query", "rewrite_tried", "rewritten_description",
              "outcome", "duration_s"]


def run(query):
    """One run: the session, its trace, its log record, and any crash."""
    trace_module.start_trace()
    session, crash = None, None
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            session = run_agent(query, get_example_wardrobe())
        except Exception as exc:  # noqa: BLE001
            crash = f"{type(exc).__name__}: {exc}"
    text = trace_module.get_trace()
    last = run_log.read(1)
    record = last[0] if last and last[0].get("query") == query else None
    return {
        "query": query,
        "session": session or {},
        "crash": crash,
        "rewrites": text.count("] rewrite_description"),
        "searches": text.count("] search_listings"),
        "record": record,
    }


def row(r, passed, why=""):
    s = r["session"]
    return {
        "query": r["query"],
        "rewritten": s.get("rewritten_description"),
        "selected": (s.get("selected_item") or {}).get("id"),
        "outcome": (r["record"] or {}).get("outcome") or ("crashed" if r["crash"] else None),
        "rewrites": r["rewrites"],
        "searches": r["searches"],
        "pass": passed,
        "why": why,
    }


def trial(label, n):
    config.CACHE_ENABLED = False
    results = {}

    # Criteria 1, 2a and 5: the five fixable queries, twice each.
    fixable_runs = [run(q) for q in FIXABLE for _ in range(2)]

    rows = []
    for r in fixable_runs:
        item = (r["session"].get("selected_item") or {}).get("id")
        ok = (not r["crash"] and r["session"].get("fit_card")
              and item in FIXABLE[r["query"]])
        rows.append(row(r, bool(ok), "" if ok else "no fit card on an allowed listing"))
    results["1"] = rows

    rows = []
    for r in fixable_runs:
        ok = r["rewrites"] <= 1 and r["searches"] <= 2 and not r["crash"]
        rows.append(row(r, ok, "" if ok else "more than one rewrite or two searches"))
    for q in MATCHING:
        for _ in range(2):
            r = run(q)
            rec = r["record"] or {}
            ok = not r["crash"] and r["rewrites"] == 0 and rec.get("rewrite_tried") is False
            rows.append(row(r, ok, "" if ok else "rewrite ran on a search that had results"))
    results["2"] = rows

    rows = []
    for q in IMPOSSIBLE:
        for _ in range(2):
            r = run(q)
            s = r["session"]
            msg = s.get("error") or ""
            rewritten = s.get("rewritten_description")
            ok = (not r["crash"] and (r["record"] or {}).get("outcome") == "stopped"
                  and s.get("selected_item") is None
                  and msg.startswith("No listings matched")
                  and (rewritten is None or rewritten in msg)
                  and s.get("fit_card") is None and s.get("outfit_suggestion") is None)
            rows.append(row(r, ok, "" if ok else f"message: {msg[:80]}"))
    results["3"] = rows

    rows = []
    real_model = config.MODEL
    config.MODEL = "no-such-model"
    try:
        for q in FIXABLE:
            r = run(q)
            rec = r["record"] or {}
            ok = (not r["crash"] and rec.get("outcome") == "stopped"
                  and bool(r["session"].get("error")))
            rows.append(row(r, ok, "" if ok else f"crash={r['crash']} record={bool(rec)}"))
    finally:
        config.MODEL = real_model
    results["4"] = rows

    rows = []
    for r in fixable_runs:
        rec = r["record"]
        missing = [f for f in LOG_FIELDS if rec is None or f not in rec]
        ok = rec is not None and not missing and isinstance(rec.get("duration_s"), (int, float))
        rows.append(row(r, ok, "" if ok else f"missing: {missing}"))
    results["5"] = rows

    out = config.RESULTS_DIR / f"capstone_{label}_trial{n}.json"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"label": label, "trial": n,
                   "finished": datetime.now().isoformat(timespec="seconds"),
                   "criteria": results}, f, indent=2, ensure_ascii=False)

    print(f"Trial {n} ({label}):")
    for c, rows in results.items():
        print(f"  criterion {c}: {sum(r['pass'] for r in rows)}/{len(rows)}")
    print(f"Wrote {out}")


TARGETS = {
    "1": ("Rewrite finds an allowed listing", 7, "7 of 10"),
    "2": ("At most one rewrite; none when search has results", 20, "20 of 20"),
    "3": ("Impossible query stops with a clear message", 10, "10 of 10"),
    "4": ("Model down: stopped, not crashed, and logged", 5, "5 of 5"),
    "5": ("Every run has a complete log record", 10, "10 of 10"),
}


def summary(label):
    trials = []
    for n in (1, 2, 3):
        path = config.RESULTS_DIR / f"capstone_{label}_trial{n}.json"
        with open(path, encoding="utf-8") as f:
            trials.append(json.load(f)["criteria"])

    lines = [f"# Capstone run log ({label})", "",
             "| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |",
             "|---|---|---|---|---|---|"]
    for c, (name, need, target) in TARGETS.items():
        counts = [sum(r["pass"] for r in t[c]) for t in trials]
        total = len(trials[0][c])
        verdict = "MET" if all(k >= need for k in counts) else "MISSED"
        lines.append(f"| {c}. {name} | {target} | "
                     + " | ".join(f"{k}/{total}" for k in counts)
                     + f" | {verdict} |")

    lines += ["", "## Criterion 1, every attempt", "",
              "| Trial | Query | Rewritten to | Selected | Pass |", "|---|---|---|---|---|"]
    for i, t in enumerate(trials, 1):
        for r in t["1"]:
            lines.append(f"| {i} | {r['query']} | {r['rewritten']} | {r['selected']} | "
                         f"{'yes' if r['pass'] else 'no'} |")

    text = "\n".join(lines)
    print(text)
    out = config.RESULTS_DIR / f"capstone_{label}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--label", required=True)
    p.add_argument("--trial", type=int)
    p.add_argument("--summary", action="store_true")
    a = p.parse_args()
    summary(a.label) if a.summary else trial(a.label, a.trial)