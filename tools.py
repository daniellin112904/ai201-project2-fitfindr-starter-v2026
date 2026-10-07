"""
The three FitFindr tools.

    search_listings(description, size, max_price)  -> list[dict]
    suggest_outfit(new_item, wardrobe)             -> str
    create_fit_card(outfit, new_item)              -> str

Each one is standalone and testable on its own. The full spec of inputs,
returns and empty cases is in the README under Tool Inventory.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# Words that say nothing about which listing someone wants.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "in", "on", "of", "to", "with",
    "i", "im", "looking", "want", "need", "some", "something", "any",
    "under", "below", "size", "sized", "length", "please", "me", "my",
}


def _tokens(text: str | None) -> list[str]:
    """Lowercase letter/digit words, with a trailing plural 's' dropped."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def _size_tokens(size: str | None) -> set[str]:
    """Split a size string on anything that isn't a letter or digit.

    "S/M" -> {"s", "m"}, "XL (oversized)" -> {"xl", "oversized"},
    "W30 L30" -> {"w30", "l30"}. Matching on whole tokens is what stops
    "l" matching "xl" and "s" matching "us 9".
    """
    return set(re.findall(r"[a-z0-9]+", (size or "").lower()))


def _price_text(item: dict) -> str:
    return f"${float(item.get('price') or 0):.2f}"


def _item_summary(item: dict) -> str:
    """A one-paragraph description of a listing for a model prompt."""
    colors = ", ".join(item.get("colors") or []) or "not listed"
    tags = ", ".join(item.get("style_tags") or []) or "none"
    brand = item.get("brand") or "no brand listed"
    return (
        f"{item.get('title', 'Unknown item')} ({item.get('category', 'item')}), "
        f"size {item.get('size', 'unknown')}, {_price_text(item)} on "
        f"{item.get('platform', 'an unknown platform')}, condition "
        f"{item.get('condition', 'unknown')}, colors: {colors}, "
        f"style tags: {tags}, brand: {brand}."
    )


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Filter listings by price and size, then rank by keyword overlap.

    Returns a list of listing dicts, best match first, at most
    config.SEARCH_RESULT_LIMIT long. Returns [] when nothing matches.
    """
    query_words = {w for w in _tokens(description) if w not in _STOPWORDS}
    wanted_size = _size_tokens(size) if size else set()

    scored: list[tuple[int, dict]] = []
    for listing in load_listings():
        if max_price is not None and float(listing.get("price") or 0) > max_price:
            continue
        if wanted_size and not wanted_size <= _size_tokens(listing.get("size")):
            continue

        tags = " ".join(listing.get("style_tags") or [])
        title_and_tags = set(_tokens(f"{listing.get('title')} {tags}"))
        everything = set(_tokens(" ".join([
            listing.get("title") or "",
            listing.get("description") or "",
            listing.get("category") or "",
            listing.get("brand") or "",
            tags,
            " ".join(listing.get("colors") or []),
        ])))

        # A word found anywhere counts once; found in the title or tags, it
        # counts again, so "graphic tee" in the title outranks a passing
        # mention in the description.
        score = len(query_words & everything) + len(query_words & title_and_tags)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Ask the model for two outfits built around new_item.

    With wardrobe items, the outfits use those pieces by name. With an empty
    wardrobe, they use common basics instead. Always returns a non-empty string.
    """
    items = (wardrobe or {}).get("items") or []
    summary = _item_summary(new_item)

    if not items:
        prompt = (
            "A shopper is thinking about buying this thrifted item:\n"
            f"{summary}\n\n"
            "They have not shared their wardrobe. Suggest two outfits built "
            "around this item using common basics most people own. Name each "
            "piece specifically, for example 'white high-top sneakers' rather "
            "than 'shoes'. Keep it under 120 words, as two short labelled outfits."
        )
    else:
        owned = "\n".join(
            f"- {w.get('name')} ({w.get('category')}; colors: "
            f"{', '.join(w.get('colors') or []) or 'not listed'})"
            for w in items
        )
        prompt = (
            "A shopper is thinking about buying this thrifted item:\n"
            f"{summary}\n\n"
            "Here is what they already own:\n"
            f"{owned}\n\n"
            "Suggest two outfits that pair the new item with pieces from their "
            "wardrobe. Name the wardrobe pieces exactly as written above and only "
            "use pieces from that list. Keep it under 120 words, as two short "
            "labelled outfits."
        )

    response = (generate(prompt) or "").strip()
    if not response:
        return (
            f"No outfit ideas came back for {new_item.get('title', 'this item')}. "
            "Try running it again."
        )
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Ask the model for a two to four sentence caption about the find.

    Returns a fixed message, without calling the model, if outfit is empty.
    """
    if not outfit or not outfit.strip():
        return "No fit card: there was no outfit suggestion to build a caption from."

    prompt = (
        "Write a caption someone would actually post on Instagram or TikTok "
        "about a thrift find.\n\n"
        f"The find: {_item_summary(new_item)}\n\n"
        f"How they plan to wear it:\n{outfit}\n\n"
        "Rules:\n"
        "- Two to four sentences, first person, casual, like a real post.\n"
        f"- Mention the item, the price ({_price_text(new_item)}) and the "
        f"platform ({new_item.get('platform', 'the app')}) once each.\n"
        "- Be specific about the vibe of the outfit.\n"
        "- Do not mention a brand unless one is listed above.\n"
        "- At most two hashtags.\n"
        "- Return only the caption, nothing else."
    )
    return (generate(prompt) or "").strip()