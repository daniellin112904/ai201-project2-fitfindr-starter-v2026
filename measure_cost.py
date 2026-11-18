"""
Measure what one FitFindr run costs (capstone, Milestone 3).

Runs one query N times with the cache OFF, so every run makes real model
calls, then averages the tokens, model calls and seconds that run_log.py
recorded for those runs.

    python measure_cost.py 'comfy sweater'          10 runs
    python measure_cost.py 'comfy sweater' -n 5
"""

import argparse
import io
import contextlib
from statistics import mean

import config
import run_log
from agent import run_agent
from utils.data_loader import get_example_wardrobe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("-n", type=int, default=10)
    args = parser.parse_args()

    config.CACHE_ENABLED = False  # every run pays for its own model calls

    for i in range(1, args.n + 1):
        with contextlib.redirect_stdout(io.StringIO()):  # hide the trace
            run_agent(args.query, get_example_wardrobe())
        r = run_log.read(1)[0]
        print(f"run {i:>2}: {r['outcome']:<8} calls {r['model_calls']}  "
              f"tokens {r['prompt_tokens']} + {r['output_tokens']}  "
              f"{r['duration_s']:.2f}s  rewrite={r['rewritten_description']}")

    runs = run_log.read(args.n)
    print(f"\nAverage over {len(runs)} runs of '{args.query}', cache off:")
    print(f"  model calls    {mean(r['model_calls'] for r in runs):.1f}")
    print(f"  prompt tokens  {mean(r['prompt_tokens'] for r in runs):.0f}")
    print(f"  output tokens  {mean(r['output_tokens'] for r in runs):.0f}")
    print(f"  seconds        {mean(r['duration_s'] for r in runs):.2f}")


if __name__ == "__main__":
    main()