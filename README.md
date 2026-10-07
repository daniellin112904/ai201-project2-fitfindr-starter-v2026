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

- *What I asked for:* I asked Claude to write the code for all three tools and the planning loop.
- *What came back:* Everything at once: the full `tools.py`, the parsing helpers and loop for `agent.py`, and the README specs in a single reply.
- *What I changed:* I couldn't check that much code at once, so I had it go one step at a time instead: README specs first, then each tool on its own, tested from the terminal against its spec (including the empty case) before moving on, and only then the loop. That ordering is why every tool's output in Sample Run was checked before the loop used it.

**Moment 2**

- *What I asked for:* Help turning "the fit card shouldn't get the price or platform wrong" into criterion 4.
- *What came back:* Claude pointed out that the model might write the price as "$24", "$24.00", or "24 bucks", so "contains the price" would be judged differently from one run to the next.
- *What I changed:* I wrote the criterion to say exactly what counts: a dollar sign followed by the whole-dollar amount, with the platform matched ignoring capitalization. When I then ran the fit card three times, all three wrote "$38.00" and "depop", which that definition counts as a pass.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
