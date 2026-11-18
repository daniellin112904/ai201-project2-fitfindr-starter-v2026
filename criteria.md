# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. _"The agent handles errors"_ is an opinion.
_"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"_ is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; _"80% seemed reasonable"_ does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
My search is plain keyword matching, so a query that uses different words
from the listing, like "running shoes" when the listing says "sneakers",
finds nothing even though a match exists. I allow one miss for that. My test
queries will use words that appear in the listings, so missing more than one
would mean the search or the loop is broken, not just the wording.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The empty check is a single `if` on the list `search_listings` returns, and
the empty path never calls the model. Search is deterministic, so the same
impossible query produces the same empty list every time. Criterion 1 allows
a miss because wording and model output vary; nothing varies here, so a
single failure would mean the branch itself is broken.

---

## 3. The item search found is the item the next tools receive

For 5 of 5 matching queries, the `id` of `session["selected_item"]` after the
run equals the `id` of `session["search_results"][0]`.

**Why this target:**
Moving the item through the session is plain code with no model involved, so
it should behave the same way every run. Any mismatch would mean the loop
picked or overwrote the wrong item, which is a state bug rather than variation,
so I allow no misses.

---

## 4. The fit card gets the price and platform right

In at least 4 of 5 runs on matching queries, the fit card contains the selected
item's price written as a dollar sign followed by its whole-dollar amount (for
a $24.00 listing, "$24" or "$24.00" both count) and the selected item's
platform name, ignoring capitalization.

**Why this target:**
A caption with the wrong price or platform would send someone to the wrong
place or set the wrong expectation, which is worse than a clumsy sentence. The
prompt gives the model both values directly, so it should usually copy them.
I allow one miss because the model writes at temperature 0.9 and may phrase the
price loosely, like "24 bucks", or drop a detail; more than one miss would mean
the prompt isn't controlling the output.

---

## 5. The search respects the price ceiling

For 5 of 5 queries that state a maximum price, no listing in
`session["search_results"]` has a price above that maximum.

**Why this target:**
If I ask for something under $50 and get a $75 listing, the agent has ignored a
constraint I gave it, which makes every other result untrustworthy. The price
filter is a plain comparison with no model involved, so it should never fail.
The real risk is upstream: if `parse_query` misses the price, `max_price`
becomes None and no filter runs at all. Checking every result rather than just
the first catches that, and any miss would be a parsing or filtering bug, so I
allow none.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Capstone Criteria — Rewrite on Empty Search

Written before any capstone results existed. Every run below has the cache off (`AI201_CACHE=0`), so each one makes real model calls.

**Test queries.** Five fixable queries return nothing on the first search, but the listings have the item under different words. The listing IDs after each one are the items that count as a correct match, decided before running anything:

| Fixable query   | Counts as a match                                                                                       |
| --------------- | ------------------------------------------------------------------------------------------------------- |
| comfy sweater   | lst_008 (knit cardigan), lst_012 (crewneck sweatshirt), lst_027 (college crewneck), lst_030 (knit vest) |
| purse           | lst_039 (mini shoulder bag)                                                                             |
| running shoes   | lst_019 (platform sneakers), lst_035 (canvas sneakers)                                                  |
| button up shirt | lst_029 (silk button-down), lst_003 (flannel shirt)                                                     |
| ankle booties   | lst_028 (suede chelsea boots)                                                                           |

Five impossible queries can never match, because each has a price limit of $5 and the cheapest listing is $12: `designer ballgown size XXS under $5`, `tuxedo under $5`, `winter coat size XXS under $5`, `swimsuit under $5`, `ski goggles under $5`.

## 1. Query Rewrite Success

Out of 10 attempts (each of the 5 fixable queries run twice), at least 7 of 10 should end with a fit card built on one of the listings named for that query in the table above. One trial is all 10 attempts; I run three trials and the target has to hold in all three.

**Why this target:**
I chose 70% because the rewrite feature should successfully recover most searches that fail due to different wording. I don't expect it to be perfect because the model might choose words that still don't match the listings. However, anything below 70% would make the feature less useful.

## 2. Rewrite and Retry Limit

For the 10 attempts in criterion 1, all 10 should run `rewrite_description` at most once and `search_listings` at most twice, as counted in the trace. For 10 searches that already return results (`vintage graphic tee under $30`, `denim jacket under $50`, `90s track jacket in size M`, `platform sneakers size 8`, `silk slip dress in midi length under $40`, each run twice), none should run `rewrite_description`, so `rewrite_tried` is `false` in all 10 log records.

**Why this target:**
I chose 100% because the agent should not repeatedly rewrite the same query or make unnecessary model calls. Limiting retries prevents infinite loops, reduces token usage, and keeps the system from wasting time on searches that may never succeed.

## 3. Unsuccessful Rewrite Handling

For 10 searches where neither the original query nor the rewritten query matches any listing (each of the 5 impossible queries run twice), all 10 should end with `outcome` = `stopped`, no selected item, and a message that starts with "No listings matched". When a rewrite was made (`rewritten_description` is not null), the message should also include that rewritten query. No fit card or outfit should be produced.

**Why this target:**
I chose 100% because the system should never invent products when it cannot find a match. Even when the rewrite fails, users should understand what the agent tried and why it couldn't recommend anything.

## 4. Model Failure Handling

When the rewriting model is unavailable (simulated by setting `AI201_MODEL` to a model name that doesn't exist, then running each of the 5 fixable queries once), all 5 of 5 attempts should end with `outcome` = `stopped` rather than `crashed`, show the user a message instead of a traceback, and have a record in `logs/runs.jsonl`.

**Why this target:**
I chose 100% because external model services can fail, and the agent should handle those failures without crashing or misleading the user. Recording errors is also important because it allows me to identify what went wrong afterward.

## 5. Structured Logging

Across the 10 runs in criterion 1, all 10 should produce a JSON record in `logs/runs.jsonl` containing a timestamp, the original query, whether rewriting was attempted, the rewritten query when applicable, the final outcome, and the execution duration (`timestamp`, `query`, `rewrite_tried`, `rewritten_description`, `outcome`, `duration_s`).

**Why this target:**
I chose 100% because logging is necessary to understand how the new feature performs. If some runs are missing, I wouldn't be able to accurately measure rewrite success, identify failures, or compare results before and after making an improvement.
