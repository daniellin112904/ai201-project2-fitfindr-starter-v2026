# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

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
