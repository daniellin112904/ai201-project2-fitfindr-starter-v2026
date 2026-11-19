# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is a thrift shopping agent. A user types what they want in plain language, like "vintage graphic tee under $30", and the agent searches 40 secondhand listings for matches within their price and size, picks the best one, suggests two outfits pairing it with clothes the user already owns, and writes a short caption they could post about the find. If nothing in the listings matches, it stops before suggesting outfits and tells the user which filter or word to change to get results.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters `data/listings.json` by price ceiling and size, then ranks what's left by how many of the description's keywords appear in each listing's title, description, category, brand, style tags and colors.
- **Inputs:** `description` (str), `size` (str or None), `max_price` (float or None). A `None` size or price skips that filter.
- **Returns:** A list of listing dicts, best match first, at most `config.SEARCH_RESULT_LIMIT` (10) long. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Price matches when `price <= max_price`. Size matches when every token of the requested size appears among the tokens of the listing's size, split on anything that isn't a letter or digit, so `M` matches `S/M` and `M` but not `XL (oversized)`, and `8` matches `US 8`.
- **When it has nothing:** An empty list `[]`. Never `None`, never an exception. This is what the loop branches on.

### `suggest_outfit`

- **What it does:** Asks the model for two outfits built around the new item, using pieces from the user's wardrobe by name.
- **Inputs:** `new_item` (dict, a listing dict), `wardrobe` (dict with an `items` key holding a list of wardrobe item dicts).
- **Returns:** A non-empty string with two short labelled outfits, under about 120 words, naming wardrobe pieces exactly as they appear in the wardrobe.
- **When it has nothing:** With an empty wardrobe, it asks the model for two outfits using common basics instead, and still returns a non-empty string. If the model returns nothing, it returns a message naming the item and saying to try again.

### `create_fit_card`

- **What it does:** Asks the model for a short social media caption about the find and how it will be worn.
- **Inputs:** `outfit` (str, the output of `suggest_outfit`), `new_item` (dict, a listing dict).
- **Returns:** A caption string of two to four sentences that mentions the item, its price and its platform once each, with at most two hashtags, and no brand mentioned unless the listing has one.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns the string `"No fit card: there was no outfit suggestion to build a caption from."` without calling the model.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that names which filter is blocking results and what to change, and stop without calling `suggest_outfit`. Otherwise, take the first result as `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. A price ceiling comes from "under/below/less than/max/up to $N", or a bare "$N" if none of those appear. A size comes from "size X". Whatever text is left, with punctuation removed, becomes the description.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` → `selected_item` → `outfit_suggestion` → `fit_card`. On the empty path, the run stops after `search_results` with `error` set, and `selected_item`, `outfit_suggestion` and `fit_card` stay `None`. Each tool reads its inputs from the session, not from the previous call's return value.

---

## Sample Run

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   **Outfit 1: Casual Streetwear**
- Y2K Baby Tee — Butterfly Print
- Baggy straight-leg jeans, dark wash
- Vintage black denim jacket
- Chunky white sneakers
- Black crossbody bag

**Outfit 2: Edgy Contrast**
- Y2K Baby Tee — Butterfly Print
- Wide-leg khaki trousers
- Black cropped zip hoodie
- Black combat boots
- Brown leather belt

  Fit card: Scored this little $18.00 butterfly tee on Depop and I'm obsessed with the pink and purple print. Already planning to wear it with baggy dark-wash jeans and a black denim jacket for daytime, or switch it up with wide-leg khakis and combat boots for an edgy vibe. #y2k #thrifted

0 model calls this session, 2 served from cache
```

**The empty path, from `python agent.py`**

```
=== A query it can't ===
  stopped: No listings matched 'designer ballgown' in size XXS under $5. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').
  fit_card is None — it should still be None here
```

**The three tools, tested one at a time**

`search_listings`, a matching query and an impossible one:

```
$ python -c "from tools import search_listings; r = search_listings('graphic tee', max_price=30); print(len(r)); [print(x['id'], x['title'], x['price'], x['size']) for x in r]"
7
lst_002 Y2K Baby Tee — Butterfly Print 18.0 S/M
lst_006 Graphic Tee — 2003 Tour Bootleg Style 24.0 L
lst_033 Vintage Band Tee — Faded Grey 19.0 L
lst_015 Vintage Graphic Hoodie — Faded Black 26.0 L
lst_017 Mesh Long-Sleeve Top — Black 15.0 S/M
lst_011 Low-Rise Cargo Pants — Khaki 27.0 W29
lst_012 Oversized Crewneck Sweatshirt — Vintage Navy 20.0 XL (fits oversized)

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

`suggest_outfit`, with the example wardrobe and with an empty one:

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
**Outfit 1: Casual Streetwear**
* Vintage Levi's 501 Jeans — Medium Wash
* Oversized grey crewneck sweatshirt
* Chunky white sneakers
* Black crossbody bag

**Outfit 2: Edge & Contrast**
* Vintage Levi's 501 Jeans — Medium Wash
* White ribbed tank top
* Vintage black denim jacket
* Black combat boots
* Brown leather belt

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
**Outfit 1: Casual Streetwear**
*   **Top:** Black ribbed cotton crewneck t-shirt
*   **Outerwear:** Oversized tan canvas chore jacket
*   **Shoes:** White canvas low-top sneakers
*   **Accessories:** Silver chain necklace

**Outfit 2: Elevated Denim**
*   **Top:** Crisp white button-down oxford shirt (lightly tucked)
*   **Belt:** Black leather belt with a simple silver buckle
*   **Shoes:** Black leather loafers
*   **Outerwear:** Black wool overcoat
```

`create_fit_card`, three runs on the same item with the cache off, then the empty-outfit guard:

```
$ python -c "import config; config.CACHE_ENABLED = False; from tools import create_fit_card; from utils.data_loader import load_listings; item = load_listings()[0]; [print(f'--- run {i} ---', create_fit_card('Levis with an oversized grey crewneck and chunky white sneakers', item), sep='\n') for i in (1, 2, 3)]"
--- run 1 ---
Scored these vintage Levi's 501 jeans on depop for just $38.00 and they fit like an absolute dream. Can't wait to lean into the effortless streetwear vibe by pairing them with an oversized grey crewneck and chunky white sneakers.

#thrifted #streetwear
--- run 2 ---
Scored these vintage Levi's 501 jeans on depop for just $38.00 and they fit like an absolute dream. Can't wait to lean into the effortless streetwear vibe by pairing them with an oversized grey crewneck and chunky white sneakers.

#thriftfinds #levis
--- run 3 ---
Scored these vintage Levi's 501 jeans on depop for just $38.00 and the fit is genuinely unmatched. I’m living in this exact medium wash denim paired with an oversized grey crewneck and chunky white sneakers for the ultimate cozy streetwear vibe.

#thriftfinds #levis

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
No fit card: there was no outfit suggestion to build a caption from.
```

The three fit cards all mention the price and platform, but the variation is small: all three share an opening, and runs 1 and 2 differ only in their hashtags.

---

## How I Used AI

**Moment 1**

- _What I asked for:_ I asked Claude to write the code for all three tools and the planning loop.
- _What came back:_ Everything at once: the full `tools.py`, the parsing helpers and loop for `agent.py`, and the README specs in a single reply.
- _What I changed:_ I couldn't check that much code at once, so I had it go one step at a time instead: README specs first, then each tool on its own, tested from the terminal against its spec (including the empty case) before moving on, and only then the loop. That ordering is why every tool's output in Sample Run was checked before the loop used it.

**Moment 2**

- _What I asked for:_ Help turning "the fit card shouldn't get the price or platform wrong" into criterion 4.
- _What came back:_ Claude pointed out that the model might write the price as "$24", "$24.00", or "24 bucks", so "contains the price" would be judged differently from one run to the next.
- _What I changed:_ I wrote the criterion to say exactly what counts: a dollar sign followed by the whole-dollar amount, with the platform matched ignoring capitalization. When I then ran the fit card three times, all three wrote "$38.00" and "depop", which that definition counts as a pass.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

`python run_eval.py --label before`, cache off, five tries per scenario. Full
output in `results/run_2026-10-14_0159_before.md`.

| Criterion                                   | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict   |
| ------------------------------------------- | ------ | ----- | ----- | ----- | ----- | ----- | --------- |
| 1. Matching query completes all three tools | 4 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 2. Impossible query stops before tool 2     | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 3. Selected item is the first search result | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 4. Fit card states price and platform       | 4 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 5. No result above the max price            | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |

**Real output from one try of each**, from `run_eval.py` running `agent.py::run_agent`:

```
Criterion 1, "vintage graphic tee under $30", try 1:
[2] search_listings (via MCP)  out: 10 items: lst_002 Y2K Baby Tee — Butterfly Print $18.0…
[3] suggest_outfit             out: **Outfit 1** Y2K Baby Tee — Butterfly Print paired with Baggy straight-leg jeans, dark wash…
[4] create_fit_card            out: Scored this unreal butterfly print baby tee on Depop for just $18.00 and I am officially obsessed…
  try 1: completed — fit card 313 chars

Criterion 2, "designer ballgown size XXS under $5", try 1:
[2] search_listings (via MCP)  out: [] (empty)
[3] stop                       out: No listings matched 'designer ballgown' in size XXS under $5. To get results, try broader words…
  try 1: stopped early

Criterion 3, "90s track jacket in size M", try 1:
[2] search_listings (via MCP)  out: 4 items: lst_004 90s Track Jacket — Navy/White Stripe $45.0…
[3] suggest_outfit             out: **Outfit 1: Casual Streetwear** - 90s Track Jacket — Navy/White Stripe - White ribbed tank top…

Criterion 4, "denim jacket under $50", try 1:
[4] create_fit_card            out: Scored this cropped Wrangler denim jacket on Poshmark for $42.00 and I'm already obsessed…

Criterion 5, "vintage jacket under $40", every result checked against the limit:
{'description': 'vintage jacket', 'size': None, 'max_price': 40.0}
over limit: []
lst_001 bottoms 38.0 Vintage Levi's 501 Jeans — Medium Wash
lst_002 tops 18.0 Y2K Baby Tee — Butterfly Print
lst_003 tops 22.0 Oversized Flannel Shirt — Plaid Red/Black
lst_005 bottoms 32.0 Corduroy Wide-Leg Pants — Rust
lst_006 tops 24.0 Graphic Tee — 2003 Tour Bootleg Style
lst_010 outerwear 40.0 Vintage Windbreaker — Color Block Purple/Teal
lst_012 tops 20.0 Oversized Crewneck Sweatshirt — Vintage Navy
lst_013 bottoms 30.0 90s Silk Slip Dress — Floral, Midi Length
lst_014 accessories 12.0 Leather Belt — Brown, Braided
lst_015 tops 26.0 Vintage Graphic Hoodie — Faded Black
```

---

## Verdicts and Diagnoses

| #   | Criterion                     | Target | Verdict   | How I decided                                                                                                                                                                                                                |
| --- | ----------------------------- | ------ | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Matching query completes      | 4 of 5 | MET (5/5) | All five tries reached `create_fit_card` and returned a card.                                                                                                                                                                |
| 2   | Impossible query stops        | 5 of 5 | MET (5/5) | All five stopped at step 3 before `suggest_outfit`, with a message naming what to try.                                                                                                                                       |
| 3   | Selected item is first result | 5 of 5 | MET (5/5) | The first search result was `lst_004` on every try, and every outfit was built around that same track jacket. The trace prints input keys rather than values, so this is read from the outfit text rather than a printed id. |
| 4   | Fit card price and platform   | 4 of 5 | MET (5/5) | All five cards contain "Poshmark" and either "$42" or "$42.00", which my definition counts.                                                                                                                                  |
| 5   | No result over max price      | 5 of 5 | MET (5/5) | Checked every result, not only the first: none above $40. Search is deterministic, so all five tries return this same list.                                                                                                  |

**Diagnoses**

I missed nothing, which means my targets were set low. Criteria 2, 3 and 5 test plain code with no model involved, so they could only fail through a bug, and the run shows none. Criterion 1 allows a miss for wording I never tested: every scenario used words that appear in the listings. The criterion I'd tighten is 1, by adding a query with a synonym ("running shoes" for "sneakers") so it tests the weakness its own reason names.

The run also showed a failure none of the five criteria check. For "vintage jacket under $40", the agent selected **Vintage Levi's 501 Jeans**. **Where:** the `search_listings` tool's ranking. **Mechanism:** no listing under $40 contains the word "jacket", so every result matched on "vintage" alone and scored the same. Ties keep file order, and `lst_001` is the first listing in the file, so the loop selected jeans. The search treats any single matching word as a match, so when the item-type word matches nothing, it quietly falls back to listings that only share an adjective. Criteria 1, 3 and 5 all passed on this run, because none of them asks whether the selected item is the kind of thing the user asked for.

---

## Loop Trace

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: lst_002 Y2K Baby Tee — Butterfly Print $18.0…
[3] suggest_outfit
      in:  dict with keys: new_item, wardrobe_items
      out: **Outfit 1: Casual Streetwear** - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Vinta…
[4] create_fit_card
      in:  dict with keys: new_item
      out: Scored this little $18.00 butterfly tee on Depop and I'm obsessed with the pink and purple print. Already plan…
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] stop
      in:  dict with keys: reason
      out: No listings matched 'designer ballgown' in size XXS under $5. To get results, try broader words, like an item …
```

The empty path stops at step 3 and never reaches `suggest_outfit`.

**Empty wardrobe** (`--empty-wardrobe`)

```
$ python app.py ask 'platform sneakers size 8' --empty-wardrobe
  Found:    Platform Sneakers — White Chunky Sole — $48.0 on poshmark

  Outfit:   **90s Streetwear**
Pair the white platform sneakers with straight-leg light-wash denim jeans, a fitted black ribbed tank top, and an oversized vintage plaid button-down shirt worn open. Accessorize with a small black nylon shoulder bag.
```

**Model unavailable** (one character of the key changed)

```
$ python app.py ask 'black leather jacket under $80'
[3] stop
      in:  dict with keys: reason
      out: Couldn't reach the AI model, so no outfit or caption could be written. ...

  Couldn't reach the AI model, so no outfit or caption could be written. The search still found 90s Leather Bomber — Blackfor $75.0 on depop. Check that the API key in .env is correct and that you're online, then run the same query again.
```

**On the MCP move:** `search_listings` is now registered in `mcp_server.py`, and `agent.py::run_agent` calls it through `mcp_client.call_tool` instead of directly. The return value did not change: the same queries found the same listings before and after the move, and the empty search still returns `[]`. The direct import of `search_listings` stays in `agent.py` only for `_empty_message`, which re-runs the search with one filter removed to tell the user which filter is blocking results.

---

## The Improvement

**What I changed:** One condition in `tools.py::search_listings`. Before, a listing was kept if **any** query word appeared in it. Now it is kept only if **every** query word appears in it. Ranking, filters and everything else are unchanged.

**Which failure it was meant to fix:** The one in my diagnosis. For "vintage jacket under $40", no listing under $40 contains "jacket", so every result matched on "vintage" alone, they tied, and file order put Vintage Levi's 501 Jeans first. Requiring every word means a listing has to actually be a jacket to count, so when none exists under the limit, the search returns `[]` and the loop's empty branch takes over.

### Run Log — After

`python run_eval.py --label after`, cache off, five tries per scenario. Full output in `results/run_2026-10-14_0213_after.md`.

| Criterion                                   | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict   |
| ------------------------------------------- | ------ | ----- | ----- | ----- | ----- | ----- | --------- |
| 1. Matching query completes all three tools | 4 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 2. Impossible query stops before tool 2     | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 3. Selected item is the first search result | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 4. Fit card states price and platform       | 4 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |
| 5. No result above the max price            | 5 of 5 | PASS  | PASS  | PASS  | PASS  | PASS  | MET (5/5) |

The failure it targeted, before and after:

```
Before:  "vintage jacket under $40"
  [2] search_listings (via MCP)  out: 10 items: lst_001 Vintage Levi's 501 Jeans — Medium Wash $38.0…
  → selected jeans, wrote outfits and a fit card for jeans

After:   "vintage jacket under $40"
  [2] search_listings (via MCP)  out: [] (empty)
  [3] stop  out: No listings matched 'vintage jacket' under $40. To get results,
                 raise or remove the $40 limit (3 matches without it).
```

**Did it help, and how do I know:**

Yes, for the failure it targeted. Before, asking for a vintage jacket under $40 returned jeans with a confident outfit and caption. After, the agent stops and says exactly why: no vintage jacket exists under $40, but 3 exist above it. All five criteria stayed at 5/5, so the change broke nothing they measure.

It also narrowed every search. The graphic tee query went from 10 results to 3, the denim jacket query from 7 to 1, and the track jacket from 4 to 1. The selected item was the same in all three, so nothing visible changed, but the tail of loosely related results is gone.

Two costs worth stating. First, requiring every word makes the synonym problem criterion 1 names worse: a query with one word the listings don't use now returns nothing instead of a partial match. Second, criterion 5 now passes for a weaker reason: its scenario returns an empty list, and an empty list trivially has nothing over the limit, so this run no longer actually exercises the price filter on real results.

---

## What's Still Broken

No criterion is missed, so nothing here is a miss against a target. These are the gaps I know about:

**Criterion 5's scenario no longer tests anything.** After the fix, "vintage jacket under $40" returns no results, so "no result above $40" passes trivially. I would change the scenario to a query with matches on both sides of the limit, like "denim under $40", so the filter has something to exclude. I stopped because changing scenarios after the before run would mean the two runs measured different things.

**The synonym problem got worse, and nothing tests it.** All my scenarios use words that appear in the listings. "Running shoes" would have found nothing before and still finds nothing now, but a query that is mostly right with one unusual word now fails completely where it used to partly match. I would add a synonym scenario to criterion 1, as I said in my diagnosis, and if it misses, map common synonyms before searching.

**Criterion 3 is checked indirectly.** The trace prints input keys rather than values, so I read the selected item from the outfit text rather than comparing ids directly. I would have the trace print `selected_item["id"]` alongside `search_results[0]["id"]` so the check is mechanical.

**My targets were set low.** Five of five on all five criteria in both runs means none of them was close to failing. I stopped here because I ran out of time before the deadline; tightening criterion 1 with a synonym scenario is what I would do first.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

---

## Capstone

**What This Extends**

FitFindr, my multi-tool shopping agent from units 3 and 4. Right now, when `search_listings` comes back empty, the loop stops and tells the user what to change. The new capability is a rewrite step on that empty branch: the agent asks the model to rewrite the description using words the listings actually use (for example "running shoes" to "sneakers"), then searches once more. If the second search also comes back empty, the loop stops with the same message it gives today.

This comes straight from what I left broken in unit 4. My search is keyword matching, requiring every query word made the synonym problem worse, and fixing synonyms was the first thing I said I'd do next.

**The Shape**

C, extend one capability. The capability is the rewrite and retry step on the empty search branch in `agent.py::run_agent`. It runs locally (Path B), and every run writes a structured log record.

Out of scope:

- Changing how `search_listings` matches or ranks. The rewrite works around keyword matching; it doesn't replace it.
- More than one retry, or rewriting queries that already found results.
- Changing `suggest_outfit`, `create_fit_card`, or the MCP setup.
- Hosting it online. It runs locally from `RUNNING.md`.

**Running It**

Path B, local. The start command, the environment, and the steps from a clean checkout are in [RUNNING.md](RUNNING.md) under **Capstone: running it locally**. The structured log below is the committed record of it running.

**Instrumentation**

`agent.py::run_agent` wraps the loop (`_run_loop`) and writes one JSON record per run to `logs/runs.jsonl` through `run_log.py`. It logs in a `finally` block, so a run that crashes is logged before the error is raised. Every caller gets logging this way: `app.py`, `serve.py`, `run_eval.py`, and `measure_cost.py`.

| Field                                           | What it holds                                                               |
| ----------------------------------------------- | --------------------------------------------------------------------------- |
| `timestamp`                                     | When the run started, UTC                                                   |
| `query`                                         | Exactly what the user typed                                                 |
| `wardrobe_items`                                | How many wardrobe items the run had                                         |
| `description`, `size`, `max_price`              | What `parse_query` pulled out of the query                                  |
| `rewrite_tried`                                 | Whether the first search came back empty and the rewrite step ran           |
| `rewritten_description`                         | What the model reworded the search to, or `null` if it had nothing usable   |
| `results`                                       | How many listings the final search returned                                 |
| `selected_item`, `selected_title`               | The listing the outfit and fit card were built on                           |
| `outcome`                                       | `fit_card` (finished), `stopped` (ended early with a message), or `crashed` |
| `message`                                       | The message the user saw when the run stopped                               |
| `error`                                         | The exception, if the run crashed                                           |
| `duration_s`                                    | Seconds from start to finish, including any rate limit wait                 |
| `model_calls`, `prompt_tokens`, `output_tokens` | What the run spent, from `generate.py`'s counters. A cached answer costs 0  |

Thirteen records from a real session, from `python run_log.py -n 15`. The first two were served from the cache, which is why they show 0 calls. The middle ten are `measure_cost.py` with the cache off. **The last one is a deliberate failure:** I pointed the agent at a model name that doesn't exist, so it found the denim jacket, couldn't reach the model for `suggest_outfit`, and stopped with a message instead of crashing.

```json
{"timestamp": "2026-11-18T23:22:30+00:00", "query": "purse", "wardrobe_items": 10, "description": "purse", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": "bag", "results": 1, "selected_item": "lst_039", "selected_title": "Mini Shoulder Bag — Tan Leather", "outcome": "fit_card", "message": null, "error": null, "duration_s": 3.494, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"timestamp": "2026-11-18T23:22:34+00:00", "query": "designer ballgown size XXS under $5", "wardrobe_items": 10, "description": "designer ballgown", "size": "XXS", "max_price": 5.0, "rewrite_tried": true, "rewritten_description": "dress", "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'designer ballgown' in size XXS under $5. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear'). (I also tried searching for 'dress'.)", "error": null, "duration_s": 3.117, "model_calls": 0, "prompt_tokens": 0, "output_tokens": 0}
{"timestamp": "2026-11-18T23:24:01+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 5.622, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:24:07+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 2.739, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:24:10+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": "cardigan", "results": 1, "selected_item": "lst_008", "selected_title": "Knit Cardigan — Chunky Brown", "outcome": "fit_card", "message": null, "error": null, "duration_s": 7.049, "model_calls": 3, "prompt_tokens": 985, "output_tokens": 155}
{"timestamp": "2026-11-18T23:24:17+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 2.028, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:24:19+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": "cozy knitwear", "results": 1, "selected_item": "lst_008", "selected_title": "Knit Cardigan — Chunky Brown", "outcome": "fit_card", "message": null, "error": null, "duration_s": 4.89, "model_calls": 3, "prompt_tokens": 983, "output_tokens": 166}
{"timestamp": "2026-11-18T23:24:24+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": "cozy", "results": 2, "selected_item": "lst_008", "selected_title": "Knit Cardigan — Chunky Brown", "outcome": "fit_card", "message": null, "error": null, "duration_s": 5.925, "model_calls": 3, "prompt_tokens": 985, "output_tokens": 156}
{"timestamp": "2026-11-18T23:24:30+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 1.973, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:24:32+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": "cardigan", "results": 1, "selected_item": "lst_008", "selected_title": "Knit Cardigan — Chunky Brown", "outcome": "fit_card", "message": null, "error": null, "duration_s": 34.653, "model_calls": 3, "prompt_tokens": 984, "output_tokens": 158}
{"timestamp": "2026-11-18T23:25:07+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 2.609, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:25:09+00:00", "query": "comfy sweater", "wardrobe_items": 10, "description": "comfy sweater", "size": null, "max_price": null, "rewrite_tried": true, "rewritten_description": null, "results": 0, "selected_item": null, "selected_title": null, "outcome": "stopped", "message": "No listings matched 'comfy sweater'. To get results, try broader words, like an item type ('jacket', 'dress', 'jeans') or a style ('vintage', 'y2k', 'streetwear').", "error": null, "duration_s": 3.192, "model_calls": 1, "prompt_tokens": 451, "output_tokens": 1}
{"timestamp": "2026-11-18T23:28:56+00:00", "query": "denim jacket under $50", "wardrobe_items": 10, "description": "denim jacket", "size": null, "max_price": 50.0, "rewrite_tried": false, "rewritten_description": null, "results": 1, "selected_item": "lst_007", "selected_title": "Denim Jacket — Light Wash, Cropped", "outcome": "stopped", "message": "Couldn't reach the AI model, so no outfit or caption could be written. The search still found Denim Jacket — Light Wash, Cropped for $42.0 on poshmark. Check that the API key in .env is correct and that you're online, then run the same query again.", "error": null, "duration_s": 5.597, "model_calls": 1, "prompt_tokens": 0, "output_tokens": 0}
```

**What I noticed in the log:** the same query, `comfy sweater`, with the rewrite at temperature 0, got four different results across ten runs: `cardigan` twice, `cozy knitwear`, `cozy`, and nothing usable six times. Temperature 0 doesn't make the model repeat itself. Earlier it looked like `comfy sweater` always became `cardigan`, but only because the cache kept handing back the same answer.

**What It Costs**

Measured with `python measure_cost.py 'comfy sweater'`: ten runs of the same query with the cache off, averaging the tokens and time that `run_log.py` recorded for each run. Token counts come from the API's own `usage_metadata`, through `generate.token_counts()`. I picked `comfy sweater` because it goes through the new rewrite step.

| Path                                              | Runs out of 10 | Model calls | Prompt + output tokens | Seconds                                  |
| ------------------------------------------------- | -------------- | ----------- | ---------------------- | ---------------------------------------- |
| Rewrite found something, then outfit and fit card | 4              | 3           | about 984 + 159        | 4.9 to 7.0 (34.7 with a rate limit wait) |
| Rewrite had nothing, stopped                      | 6              | 1           | 451 + 1                | 2.0 to 5.6                               |
| **Average per run**                               | 10             | **1.8**     | **664 + 64 = 728**     | **7.07**                                 |

The rewrite step on its own costs one call and about 451 prompt tokens, almost all of it the vocabulary list. The 7.07 second average is pulled up by one run that waited 29 seconds for the free tier's 15 calls per minute limit. Without it the average is 4.0 seconds.

**For 100 people a day**, at one run each:

```
model calls:  100 × 1.8 = 180 calls a day
tokens:       100 × 728 = 72,800 tokens a day
time:         100 × 7.07 s = 707 s, about 12 minutes of waiting in total
```

On the free tier I'm using, that costs $0 in money. The real limit is the 15 calls a minute: if all 100 people showed up in the same minute, 180 calls would take about 12 minutes to get through, so most of them would wait.

**Run Log and Verdicts**

Every run had the cache off. Each trial is its own process (`python capstone_eval.py --label before --trial N`), and the summary is `results/capstone_before.md`. The test queries and the listing IDs that count as a match are fixed in `criteria.md`, which was committed before any results.

| Criterion                                            | Target   | Run 1 | Run 2 | Run 3 | Verdict    |
| ---------------------------------------------------- | -------- | ----- | ----- | ----- | ---------- |
| 1. Rewrite finds an allowed listing                  | 7 of 10  | 5/10  | 6/10  | 7/10  | **MISSED** |
| 2. At most one rewrite; none when search has results | 20 of 20 | 20/20 | 20/20 | 20/20 | MET        |
| 3. Impossible query stops with a clear message       | 10 of 10 | 10/10 | 10/10 | 10/10 | MET        |
| 4. Model down: stopped, not crashed, and logged      | 5 of 5   | 5/5   | 5/5   | 5/5   | MET        |
| 5. Every run has a complete log record               | 10 of 10 | 10/10 | 10/10 | 10/10 | MET        |

Criterion 1 hit 7 in one trial, but the target has to hold in all three, so it's a miss.

**Real output from trial 1**, from `capstone_eval.py::trial`, with every criterion 1 attempt from `capstone_eval.py::summary`:

```
Trial 1 (before):
  criterion 1: 5/10
  criterion 2: 20/20
  criterion 3: 10/10
  criterion 4: 5/5
  criterion 5: 10/10

| Trial | Query | Rewritten to | Selected | Pass |
|---|---|---|---|---|
| 1 | comfy sweater | cozy knitwear | lst_008 | yes |
| 1 | comfy sweater | None | None | no |
| 1 | purse | bag | lst_039 | yes |
| 1 | purse | bag | lst_039 | yes |
| 1 | running shoes | athletic sneakers | None | no |
| 1 | running shoes | athletic shoes | None | no |
| 1 | button up shirt | button down shirt | None | no |
| 1 | button up shirt | button down shirt | None | no |
| 1 | ankle booties | boots | lst_028 | yes |
| 1 | ankle booties | boots | lst_028 | yes |
```

**Diagnosis of the miss.** There were 13 failures across the three trials, and 12 of them were multi-word rewrites: `athletic sneakers`, `athletic shoes`, and `button down shirt`. The other one was `comfy sweater`, where the model returned nothing usable. Every one-word rewrite found the right listing (`bag`, `boots`, `cardigan`, `sneakers`).

The stage is the hand-off from `tools.py::rewrite_description` to `tools.py::search_listings`. The mechanism: the rewrite picks each word from the vocabulary of the whole store, but my unit 4 fix makes search require every query word to appear on one listing. So each word is valid on its own, but together they describe a listing that doesn't exist. "athletic" is a style tag on a listing that isn't a shoe. The silk button-down has "button" and "down" but not "shirt", and the flannel has "shirt" but not "button down". My criterion assumed a rewrite either finds the right words or it doesn't, but the real failure was that the right words got combined.

A second, smaller cause: the rewrite runs at temperature 0, but the model still gave different answers for the same query (`comfy sweater` became `cozy knitwear`, `cardigan`, `cozy cardigan`, or nothing). Temperature 0 lowers the variation but doesn't remove it.

**The Improvement**

**What I changed:** `rewrite_description` now returns one word, the kind of item. The prompt asks for the most specific item type as a single word, and the code keeps only the last allowed word the model returns, since the item type usually comes last ("athletic sneakers" keeps "sneakers").

**Why:** the diagnosis showed 12 of 13 failures came from combining words from different listings, and every one-word rewrite worked.

**Did it help:** I didn't do a live rerun with the fix, because I ran out of time before Demo Day. Instead, I replayed the fix against the 30 rewrites the model actually gave in the before run, keeping only the last word of each and searching for it:

| Logged rewrite    | Kept     | First result            | Allowed? |
| ----------------- | -------- | ----------------------- | -------- |
| athletic sneakers | sneakers | lst_019                 | yes      |
| athletic shoes    | shoes    | lst_009 (Mary Janes)    | **no**   |
| button down shirt | shirt    | lst_003 (flannel shirt) | yes      |
| cozy knitwear     | knitwear | lst_008                 | yes      |
| cozy cardigan     | cardigan | lst_008                 | yes      |

| Criterion 1           | Run 1 | Run 2 | Run 3 |
| --------------------- | ----- | ----- | ----- |
| Before (live)         | 5/10  | 6/10  | 7/10  |
| Replayed with the fix | 8/10  | 8/10  | 10/10 |

The replay would meet the target in all three trials, but it isn't a measurement. It assumes the model gives the same words it did before, and the new prompt changes what the model says. The fix also creates a new risk: `athletic shoes` still fails, because "shoes" is too general and the first shoe listing is Mary Janes. One word fixes combining the wrong words, but it can make a rewrite too broad.

**What's Still Broken**

- **Criterion 1 is unverified after the fix.** What I'd do: run `python capstone_eval.py --label after` three times, exactly like the before run. Why I stopped: I ran out of time before Demo Day, and each set of three trials takes about 12 minutes because of the free tier's 15 calls a minute.
- **A one-word rewrite can be too general.** `athletic shoes` becomes `shoes` and lands on the Mary Janes. What I'd do: rank the results of a rewritten search so the listing closest to the original query comes first, instead of keeping file order.
- **The model sometimes returns nothing usable** (`comfy sweater` about half the time in the cost run). What I'd do: show the model a few real listing titles as examples, not only a word list.
- **What I'd do first, and why:** the live after run. Every other fix depends on knowing whether the one-word change actually works with the real model, and right now I only have a replay.

**How I Used AI**

**Moment 1**

- _What I asked for:_ Help building a feature that rewrites a search when nothing matches, plus the logging and cost measurement around it.
- _What came back:_ Claude wrote `rewrite_description`, the rewrite branch in `run_agent`, `run_log.py`, and `measure_cost.py`. It limited the rewrite to words that appear in the listings so the model couldn't invent search terms. It also added a comment saying temperature 0 would give the same answer every time.
- _What I changed:_ The cost run with the cache off proved that comment wrong: the same query got four different rewrites in ten runs. I kept that as a finding instead of hiding it, and it changed how I read every later result.

**Moment 2**

- _What I asked for:_ I wrote my five criteria myself, then asked Claude to check each one: how would you test it, would two people score it the same, and what would make it fail.
- _What came back:_ It flagged that "a relevant item" in criterion 1 and "a clear message" in criterion 3 could be scored differently by two people. When I asked it to fix them, it added the definitions: the exact test queries, the listing IDs that count as a match, and what the stop message has to contain. After the run, it pointed out that 12 of my 13 misses were multi-word rewrites.
- _What I changed:_ I reviewed the definitions and committed them before running anything, so the targets couldn't move after I saw results. I chose the one-word fix because it was aimed directly at that diagnosis, and I reported the after result as a replay rather than claiming a measurement I didn't run.
