#!/usr/bin/env python3
"""Rank installed skills against a goal, using catalog.json from build_catalog.py.

Usage:
  python find_skill.py "make an instagram reel about my offer"   # top matches
  python find_skill.py --category "SEO"                           # list one category
  python find_skill.py --categories                               # category counts
  python find_skill.py --top 15 "review my python code"
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set("a an and are as at be by can do for from get help how i in into is it its me my need of on or "
           "please some something that the this to up use want we what which with you your".split())
# Everyday words mapped to the words skills actually use.
SYNONYMS = {
    "reel": "video short-form instagram", "reels": "video short-form instagram", "clip": "video",
    "animation": "motion animate gsap", "animate": "motion animation", "film": "video cinematic",
    "post": "post social caption", "posts": "post social caption", "ig": "instagram", "insta": "instagram",
    "google": "seo search", "rank": "seo ranking", "ranking": "seo", "traffic": "seo",
    "client": "sales proposal outreach", "clients": "sales outreach leads", "cold": "outreach prospect",
    "quote": "proposal pricing", "quotation": "proposal", "invoice": "invoice proposals billing",
    "price": "pricing", "offer": "offer hormozi", "pitch": "pitch hormozi",
    "website": "website landing frontend", "site": "website", "landing": "landing page website",
    "bug": "debug fix review", "fix": "fix debug build", "test": "test testing tdd", "tests": "testing tdd",
    "pr": "pull request review", "deck": "slides pptx presentation", "slides": "pptx presentation",
    "spreadsheet": "xlsx excel", "excel": "xlsx", "word": "docx", "contract": "contract legal nda",
    "browse": "browser web", "scrape": "scrape web research", "research": "research search",
    "logo": "design brand", "ui": "ui design frontend", "chart": "chart dashboard dataviz",
}


def tokens(s):
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in STOP and len(w) > 1]


def expand(words):
    """(word, weight) pairs: the user's own words count fully, synonyms half."""
    out = [(w, 1.0) for w in words]
    for w in words:
        out += [(x, 0.5) for x in SYNONYMS.get(w, "").split() if x not in words]
    return out


def score(entry, words):
    name = entry["name"].lower()
    name_toks = set(re.findall(r"[a-z0-9]+", name))
    name_toks |= {t[:-1] for t in name_toks if t.endswith("s")}  # "proposals" matches "proposal"
    cat = entry["category"].lower()
    desc = entry["description"].lower()
    s = 0.0
    for w, wt in words:
        if w in name_toks:
            s += 6 * wt
        elif w in name:
            s += 3 * wt
        if w in cat:
            s += 2 * wt
        if re.search(r"\b" + re.escape(w), desc):
            s += (1 + min(desc.count(w), 3) * 0.3) * wt
    if entry["source"] in ("user", "built-in") or entry["category"] == "Mebarez (own)":
        s *= 1.15  # prefer the user's own and core skills on ties
    return s


def load():
    path = os.path.join(HERE, "catalog.json")
    if not os.path.exists(path):
        sys.exit(f"No catalog at {path}. Run: python {os.path.join(HERE, 'scripts', 'build_catalog.py')}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def show(e, s=None):
    head = f"{e['invoke']}" + (f"  (score {s:.1f})" if s is not None else "")
    print(f"{head}\n  category: {e['category']}   source: {e['source']}\n  use when: {e['use_when']}\n  path: {e['path']}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("goal", nargs="*")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--category", help="list every skill in a category (substring match)")
    ap.add_argument("--categories", action="store_true", help="list categories with counts")
    args = ap.parse_args()
    data = load()
    items = data["skills"]
    print(f"[catalog: {data['meta']['count']} skills, built {data['meta']['generated']}]")

    if args.categories:
        counts = {}
        for e in items:
            counts[e["category"]] = counts.get(e["category"], 0) + 1
        for c, n in counts.items():
            print(f"{n:4}  {c}")
        return
    if args.category:
        for e in items:
            if args.category.lower() in e["category"].lower():
                print(f"{e['invoke']:45} {e['use_when'][:110]}")
        return
    words = expand(tokens(" ".join(args.goal)))
    if not words:
        sys.exit("Give a goal, e.g.  find_skill.py \"make a promo video\"")
    ranked = sorted(((score(e, words), e) for e in items), key=lambda t: -t[0])
    ranked = [t for t in ranked if t[0] > 0][: args.top]
    if not ranked:
        print("No match. Try other words, or --categories.")
    for s, e in ranked:
        show(e, s)


if __name__ == "__main__":
    main()
