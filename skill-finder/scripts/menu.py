#!/usr/bin/env python3
"""Print the HTML for the clickable skill menu (passed verbatim to the show_widget tool).

Usage:
  python menu.py                         # category grid
  python menu.py --category "Video"      # skills in one category (substring match)
"""
import argparse
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS = {
    "Mebarez (own)": "star", "Legal": "scale", "Finance & Accounting": "receipt",
    "HR & People": "users", "Customer Support": "headset", "Operations": "settings-automation",
    "Product Management": "map", "Science & Health": "flask", "Sales & Outreach": "target-arrow",
    "Video & Motion": "movie", "SEO & AI Search": "search", "Social Media & Content": "brand-instagram",
    "Offers, Pricing & Business Strategy": "tag", "Marketing & Brand": "speakerphone",
    "Docs, PDF & Office files": "file-text", "Design, UI & Websites": "palette",
    "Data & Analytics": "chart-bar", "Research & Web Browsing": "world-search",
    "Productivity & Claude Setup": "adjustments", "Dev: Code Review & Quality": "code",
    "Dev: Agents, Planning & Workflow": "git-branch", "Dev: Languages, Frameworks & Infra": "server",
    "Other": "dots",
}

STYLE = """<style>
.sf-g{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px}
.sf-c,.sf-r{display:flex;align-items:center;gap:10px;text-align:left;width:100%;background:var(--surface-2);border:0.5px solid var(--border);border-radius:var(--radius);cursor:pointer;font:inherit;color:var(--text-primary)}
.sf-c{padding:10px 12px;font-size:14px}.sf-r{padding:8px 12px;margin:0 0 6px}
.sf-c:hover,.sf-r:hover{border-color:var(--border-strong);background:var(--surface-1)}
.sf-c i{font-size:18px;color:var(--text-secondary)}.sf-n{margin-left:auto;font-size:12px;color:var(--text-muted)}
.sf-r code{font-family:var(--font-mono);font-size:13px;white-space:nowrap}.sf-h{font-size:13px;color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.sf-bar{display:flex;gap:8px;align-items:center;margin:0 0 12px}
</style>"""

SCRIPT = """<script>
document.querySelectorAll('[data-p]').forEach(b=>b.addEventListener('click',()=>sendPrompt(b.dataset.p)));
document.querySelectorAll('[data-s]').forEach(b=>b.addEventListener('click',()=>sendPrompt('Run the '+b.dataset.s+' skill. Ask me what I need it for first if you need details.')));
const q=document.getElementById('sf-q');
if(q&&document.getElementById('sf-go')){const go=()=>{const v=q.value.trim();const e=document.getElementById('sf-err');if(!v){e.textContent='Type what you want to do first';return}e.textContent='';sendPrompt('/skill-finder '+v)};document.getElementById('sf-go').addEventListener('click',go);q.addEventListener('keydown',ev=>{if(ev.key==='Enter')go()});q.addEventListener('input',()=>{document.getElementById('sf-err').textContent=''})}
if(q&&!document.getElementById('sf-go')){q.addEventListener('input',()=>{const v=q.value.toLowerCase();document.querySelectorAll('.sf-r').forEach(r=>{r.style.display=r.textContent.toLowerCase().includes(v)?'':'none'})})}
</script>"""


def esc(s):
    return html.escape(s or "", quote=True)


def load():
    path = os.path.join(HERE, "catalog.json")
    if not os.path.exists(path):
        sys.exit(f"No catalog at {path}. Run build_catalog.py first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def root(data):
    counts = {}
    for e in data["skills"]:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    out = [STYLE, f'<h2 class="sr-only">Skill menu: {data["meta"]["count"]} installed skills in {len(counts)} categories</h2>',
           '<div class="sf-bar"><input id="sf-q" placeholder="Make a promo video with captions" style="flex:1">'
           '<button id="sf-go">Find skill ↗</button></div>'
           '<div id="sf-err" style="font-size:13px;color:var(--text-danger);margin:-6px 0 8px"></div>',
           '<div class="sf-g">']
    for c, n in counts.items():
        out.append(f'<button class="sf-c" data-p="{esc("/skill-finder category: " + c)}">'
                   f'<i class="ti ti-{ICONS.get(c, "folder")}" aria-hidden="true"></i>{esc(c)}<span class="sf-n">{n}</span></button>')
    out.append("</div>")
    out.append(f'<p style="font-size:12px;color:var(--text-muted);margin:12px 0 0">Catalog built {data["meta"]["generated"]}</p>')
    out.append(SCRIPT)
    return "".join(out)


def category(data, name):
    items = [e for e in data["skills"] if name.lower() in e["category"].lower()]
    if not items:
        sys.exit(f"No category matches '{name}'.")
    cat = items[0]["category"]
    items = [e for e in items if e["category"] == cat]
    out = [STYLE, f'<h2 class="sr-only">{esc(cat)}: {len(items)} skills</h2>',
           f'<div class="sf-bar"><button data-p="/skill-finder"><i class="ti ti-arrow-left" aria-hidden="true"></i> All categories ↗</button>'
           f'<span style="font-size:14px;font-weight:500">{esc(cat)}</span><span class="sf-n">{len(items)}</span></div>']
    if len(items) > 12:
        out.append('<input id="sf-q" placeholder="Filter this list" style="width:100%;margin:0 0 10px">')
    for e in items:
        hint = e["use_when"] or e["description"]
        hint = hint if len(hint) <= 80 else hint[:79].rsplit(" ", 1)[0] + "…"
        out.append(f'<button class="sf-r" data-s="{esc(e["invoke"])}">'
                   f'<code>{esc(e["invoke"])}</code><span class="sf-h">{esc(hint)}</span></button>')
    out.append(SCRIPT)
    return "".join(out)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category")
    args = ap.parse_args()
    data = load()
    print(category(data, args.category) if args.category else root(data))


if __name__ == "__main__":
    main()
