#!/usr/bin/env python3
"""Scan every Claude Code skill source on this machine and build a categorized catalog.

Sources scanned:
  1. Project skills      <project>/.claude/skills/<name>/SKILL.md     -> /<name>
  2. User skills         ~/.claude/skills/<name>/SKILL.md              -> /<name>
  3. CLI plugins         ~/.claude/plugins/installed_plugins.json     -> /<plugin>:<name>
  4. Desktop-app plugins <Claude-Data>/*/rpm/*/*/plugin_*/            -> /<plugin>:<name>
  5. Anthropic skills    <Claude-Data>/*/local-agent-mode-sessions/skills-plugin/*/*/skills
                                                                      -> /anthropic-skills:<name>
  6. Built-in skills     (bundled with Claude Code, listed in BUILTINS below)

Writes catalog.json and CATALOG.md. Standard library only.

Usage:
  python build_catalog.py [--out DIR] [--project DIR ...]
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import date

HOME = os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")

# Skills that ship inside Claude Code itself (no SKILL.md on disk).
BUILTINS = {
    "code-review": "Review the current diff or a PR for bugs at a chosen effort level (low..max, or ultra in the cloud).",
    "simplify": "Clean up changed code for reuse, simplicity and efficiency, then apply the fixes.",
    "security-review": "Security review of the pending changes on the current branch.",
    "init": "Create a CLAUDE.md for the current project.",
    "loop": "Run a prompt or slash command on a repeating interval.",
    "schedule": "Create or manage scheduled cloud agents (cron routines).",
    "claude-api": "Reference for the Claude API / Anthropic SDK: models, pricing, tool use, caching.",
    "update-config": "Change Claude Code settings.json: permissions, hooks, env vars.",
    "keybindings-help": "Customize keyboard shortcuts in ~/.claude/keybindings.json.",
    "fewer-permission-prompts": "Scan past sessions and add an allowlist so you get fewer permission prompts.",
    "run": "Launch and drive this project's app to see a change working.",
    "plugin-authoring": "Make a mod: panel, status line, slash command or hook for Claude itself.",
    "workflow-authoring": "Reference for writing multi-agent Workflow scripts.",
    "artifact-design": "Design rules for published Artifact pages.",
    "artifact-capabilities": "Runtime capabilities (data, storage, viewers) for Artifact pages.",
    "artifact-diagramming": "How to draw clear diagrams inside Artifacts.",
    "dataviz": "Rules for any chart, graph or dashboard: colors, marks, accessibility.",
}

# ---------------------------------------------------------------- categories
# Order matters: first match wins. Each rule: (category, plugin names, name regex, text regex).
# "name" is matched against the invoke name, "text" against name + description.
CATEGORIES = [
    ("Mebarez (own)", [], r"^(mebarez|proposals$)", None),
    ("Legal", ["legal"], r"(contract|nda|legal|compliance-check|master-agreement)", None),
    ("Finance & Accounting", ["finance"], r"(billing-ops|finance-|invoice|tax)", None),
    ("HR & People", ["human-resources"], None, None),
    ("Customer Support", ["customer-support"], None, None),
    ("Operations", ["operations"], r"(logistics|inventory|procurement|production-scheduling|returns-reverse|carrier|customs|quality-nonconformance)", None),
    ("Product Management", ["product-management"], r"(product-lens|product-capability|plan-prd|prp-prd)", None),
    ("Science & Health", ["bio-research"], r"(healthcare|hipaa|scientific|bio)", None),
    ("Sales & Outreach", ["sales", "apollo", "common-room"],
     r"(outreach|prospect|lead-|leads|deal|social-selling|investor-outreach|connections-optimizer)", None),
    ("Video & Motion", [],
     r"^(\d\d-|remotion|gsap|hyperframes|motion|dotlottie|manim|video|fortnite|yt-edit|ecc:(remotion|manim|video|tasteforge|motion|videodb|fal-ai))",
     None),
    ("SEO & AI Search", [], r"(seo|schema$|sitemap|keyword|backlink|ai-visibility|llm-mention|ai-answer|local-pack|listing-accuracy|local-competitor|practice-area-rank|service-area-rank)", None),
    ("Social Media & Content", [],
     r"(instagram|linkedin|caption|carousel|hashtag|viral|post-|content|tiktok|youtube|threads|x-twitter|reddit|hacker-news|crosspost|social|reply-and|profile-optimizer|voice-builder|article-writing|creator|kol|audience-fit|cross-platform|scheduling-and-queue|analytics-and-reporting|x-api)",
     None),
    ("Offers, Pricing & Business Strategy", [],
     r"(hormozi|offer|pricing|bonus-stack|value-|productize|business-model|dfy-dwy|idea-to-product|effort-reduction|billion-dollar|market-research|landing-page-copy|competitive|competitor|investor-materials|customer-research|buying-signal|account-news|treatment-demand|menu-demand|restaurant-local|neighborhood|reputation-benchmark|patient-question|homeowner-question)",
     None),
    ("Marketing & Brand", ["marketing", "brand-voice"], r"(brand|marketing|email-sequence|campaign)", None),
    ("Docs, PDF & Office files", ["pdf-viewer"],
     r"(pdf|docx|pptx|xlsx|^anthropic-skills:docs$|slides|slideshow|nutrient|visa-doc|esign-field|google-workspace|documentation-lookup)", None),
    ("Design, UI & Websites", ["design"],
     r"(design|(^|[-:])(ui|ux)($|-)|figma|frontend|3d|website|redesign|interfaces|liquid-glass|taste|ios-icon|accessibility|a11y|artifact-|dataviz)",
     None),
    ("Data & Analytics", ["data"], r"(dashboard|clickhouse|sql|data-)", None),
    ("Research & Web Browsing", ["enterprise-search"],
     r"(research|browser|chrome|agent-reach|scrape|scraper|exa-search|search-first|osint|reverse-engineer|playwright|agent-browser|computer-use|iterative-retrieval)",
     None),
    ("Productivity & Claude Setup", ["productivity", "slack-by-salesforce", "cowork-plugin-management"],
     r"(memory|morning|setup|config|keybindings|explain-usage|find-skills|skill-finder|skill|hookify|instinct|session|checkpoint|aside|cost|token|context-budget|statusline|prune|learn|evolve|promote|projects$|terminal|fewer-permission|update-config|^loop$|^schedule$|^init$|plugin-authoring)",
     None),
    ("Dev: Code Review & Quality", ["engineering"],
     r"(review|refactor|quality|simplify|security|lint|coding-standards|plankton|safety-guard|gateguard|santa|verification|test-coverage|tdd|testing|e2e|regression|benchmark|codehealth|astra)",
     None),
    ("Dev: Agents, Planning & Workflow", [],
     r"(agent|loop|plan|prp|epic|harness|orch|council|workflow|devfleet|dmux|ralph|team|gan|multi-|blueprint|feature-dev|story-lifecycle|intent-driven|contract-first|change-impact|delivery-gate|git|pr$|jira|github|dev-team|claude-api|^run$|parallel|recursive-decision|architecture-decision|operator-approval)",
     None),
    ("Dev: Languages, Frameworks & Infra", [],
     r"(patterns|build|go-|golang|rust|python|java|kotlin|swift|cpp|csharp|dotnet|fsharp|perl|django|laravel|springboot|quarkus|rails|nestjs|nextjs|nuxt|vue|react|angular|flutter|dart|android|compose|bun|vite|docker|kubernetes|postgres|mysql|redis|prisma|jpa|mybatis|database|api|mcp|deployment|pm2|network|homelab|cisco|netmiko|bgp|wireguard|pihole|vlan|ito-|pytorch|mle|ml-|llm|prompt|rag|recsys|evm|defi|keccak|x402|bengali|i18n|hexagonal|backend|error-handling|latency|cache|throughput|regex|flox|uncloud|windows-desktop|tinystruct|foundation-models|nasiko|hermes|canary|deepseek|codebase|code-tour|repo-scan|codemaps|update-docs|docs-governance|living-docs)",
     None),
]
OTHER = "Other"

# Hand-picked placements for skills the rules above get wrong. Checked before the rules.
OVERRIDES = {
    "Video & Motion": ["ecc:fal-ai-media", "ecc:ui-demo", "ecc:blender-motion-state-inspection"],
    "Social Media & Content": ["caption-writer", "cross-platform-repurposing", "instagram-seo", "content-calendar",
                               "viral-captions-and-ctas", "viral-hooks", "viral-instagram-reels",
                               "viral-short-form", "viral-short-form-ideas"],
    "Design, UI & Websites": ["web-3d-motion", "figma", "design-taste-frontend", "mobile-app-ui-design",
                              "redesign-existing-projects", "ecc:frontend-design-direction", "ecc:liquid-glass-design",
                              "ecc:design-system", "ecc:gan-design", "ecc:frontend-slides"],
    "Offers, Pricing & Business Strategy": ["objection-destroyer"],
    "Research & Web Browsing": ["agent-reach", "ecc:osint-investigation", "graphify"],
    "Marketing & Brand": ["ecc:marketing-campaign", "ecc:email-ops", "ecc:mailtrap-email-integration"],
    "Productivity & Claude Setup": ["anthropic-skills:skill-creator", "ecc:ecc-guide", "ecc:ecc-recipes",
                                    "ecc:auto-update", "ecc:model-route", "ecc:strategic-compact",
                                    "ecc:messages-ops", "ecc:unified-notifications-ops", "ecc:knowledge-ops",
                                    "ecc:context-and-decisions", "ecc:ck", "ecc:workspace-surface-audit"],
    "Dev: Agents, Planning & Workflow": ["ecc:multi-frontend", "ecc:dmux-workflows", "ecc:loop-design-check",
                                         "ecc:project-init", "ecc:project-flow-ops", "ecc:ai-first-engineering",
                                         "ecc:automation-audit-ops", "ecc:opensource-pipeline", "ecc:brownfield-retrospective"],
    "Dev: Code Review & Quality": ["ecc:production-audit", "ecc:click-path-audit", "ecc:test-collaboration",
                                   "ecc:inherit-legacy-style", "ecc:rules-distill"],
    "Dev: Languages, Frameworks & Infra": ["ecc:evm-token-decimals", "ecc:cost-aware-llm-pipeline",
                                           "ecc:homelab-network-setup", "ecc:network-config-validation",
                                           "ecc:deepseek-harness-setup", "ecc:content-hash-cache-pattern",
                                           "ecc:api-design", "engineering:system-design", "ecc:nuxt4-patterns",
                                           "ecc:swiftui-patterns", "ecc:nanoclaw-repl"],
}
OVERRIDE_OF = {n: c for c, names in OVERRIDES.items() for n in names}


def categorize(invoke, plugin, description):
    name = invoke.lstrip("/").lower()
    if name in OVERRIDE_OF:
        return OVERRIDE_OF[name]
    text = (name + " " + (description or "")).lower()
    for cat, plugins, name_re, text_re in CATEGORIES:
        if plugin and plugin in plugins:
            return cat
        if name_re and re.search(name_re, name):
            return cat
        if text_re and re.search(text_re, text):
            return cat
    return OTHER


# ---------------------------------------------------------------- parsing
def parse_frontmatter(path):
    """Tiny YAML-frontmatter reader: top-level scalar keys, quoted, folded (>) and literal (|) blocks."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    text = text.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data, key, buf = {}, None, []

    def flush():
        if key is not None:
            val = " ".join(s.strip() for s in buf if s.strip())
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val.replace('\\"', '"')

    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            flush()
            key, rest = m.group(1), m.group(2)
            buf = [] if rest.strip() in (">", "|", ">-", "|-", ">+", "|+") else [rest]
        elif key is not None:
            buf.append(line)
    flush()
    return data


def use_when(desc, limit=160):
    """One-line 'use this when' hint from a description."""
    d = re.sub(r"\s+", " ", desc or "").strip()
    if not d:
        return ""
    m = re.search(r"\b(Use (?:this |it )?(?:skill )?(?:when|whenever|for|to)\b[^.]*)\.", d, re.I)
    s = m.group(1) if m else re.split(r"(?<=[.!?])\s", d, maxsplit=1)[0]
    s = s.rstrip(".")
    return s if len(s) <= limit else s[: limit - 1].rsplit(" ", 1)[0] + "…"


def short_path(p):
    p = os.path.normpath(p)
    local = os.environ.get("LOCALAPPDATA")
    if local and p.lower().startswith(os.path.normpath(local).lower()):
        p = "%LOCALAPPDATA%" + p[len(os.path.normpath(local)):]
    elif p.lower().startswith(HOME.lower()):
        p = "~" + p[len(HOME):]
    return p.replace("\\", "/")


# ---------------------------------------------------------------- sources
def claude_data_dirs():
    """Folders where the Claude desktop app keeps plugins (Windows, macOS, Linux)."""
    roots = []
    if os.environ.get("CLAUDE_DATA_DIRS"):
        roots += os.environ["CLAUDE_DATA_DIRS"].split(os.pathsep)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots += glob.glob(os.path.join(local, "Claude-Data", "*"))
    roots += glob.glob(os.path.join(HOME, "Library", "Application Support", "Claude*"))
    roots += glob.glob(os.path.join(HOME, ".config", "Claude*"))
    return [r for r in roots if os.path.isdir(r)]


def skills_in(folder):
    """Yield (name, SKILL.md path) for each <folder>/<name>/SKILL.md."""
    for p in sorted(glob.glob(os.path.join(folder, "*", "SKILL.md"))):
        yield os.path.basename(os.path.dirname(p)), p


def commands_in(folder):
    for p in sorted(glob.glob(os.path.join(folder, "*.md"))):
        yield os.path.splitext(os.path.basename(p))[0], p


def plugin_name(root, fallback):
    for rel in (".claude-plugin/plugin.json", "plugin.json"):
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                return json.load(f).get("name") or fallback
        except (OSError, ValueError):
            pass
    return fallback


def scan_plugin(root, plugin, source, add):
    for name, p in skills_in(os.path.join(root, "skills")):
        add(f"/{plugin}:{name}", p, source, plugin, "skill")
    for name, p in commands_in(os.path.join(root, "commands")):
        add(f"/{plugin}:{name}", p, source, plugin, "command")


def scan(projects):
    entries = {}

    def add(invoke, path, source, plugin, kind, desc=None):
        if invoke in entries:
            return  # first source wins (dedupes the same plugin across desktop accounts)
        fm = parse_frontmatter(path) if path else {}
        d = desc if desc is not None else fm.get("description", "")
        entries[invoke] = {
            "invoke": invoke,
            "name": invoke.lstrip("/"),
            "kind": kind,
            "source": source,
            "plugin": plugin,
            "category": categorize(invoke, plugin, d),
            "use_when": use_when(d),
            "description": re.sub(r"\s+", " ", d).strip(),
            "path": short_path(path) if path else "(built into Claude Code)",
        }

    for proj in projects:
        for name, p in skills_in(os.path.join(proj, ".claude", "skills")):
            add(f"/{name}", p, f"project:{os.path.basename(os.path.abspath(proj))}", "", "skill")

    for name, p in skills_in(os.path.join(CLAUDE, "skills")):
        add(f"/{name}", p, "user", "", "skill")

    try:
        with open(os.path.join(CLAUDE, "plugins", "installed_plugins.json"), encoding="utf-8") as f:
            installed = json.load(f).get("plugins", {})
    except (OSError, ValueError):
        installed = {}
    for key, installs in installed.items():
        for inst in installs:
            root = inst.get("installPath", "")
            if os.path.isdir(root):
                scan_plugin(root, plugin_name(root, key.split("@")[0]), "cli-plugin", add)

    for data in claude_data_dirs():
        for root in sorted(glob.glob(os.path.join(data, "rpm", "*", "*", "plugin_*"))):
            scan_plugin(root, plugin_name(root, os.path.basename(root)), "desktop-plugin", add)
        for sk in sorted(glob.glob(os.path.join(data, "local-agent-mode-sessions", "skills-plugin", "*", "*", "skills"))):
            for name, p in skills_in(sk):
                add(f"/anthropic-skills:{name}", p, "anthropic-skills", "anthropic-skills", "skill")

    for name, desc in BUILTINS.items():
        add(f"/{name}", None, "built-in", "", "skill", desc)

    order = [c[0] for c in CATEGORIES] + [OTHER]
    return sorted(entries.values(), key=lambda e: (order.index(e["category"]), e["name"]))


# ---------------------------------------------------------------- output
def md_cell(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


def write_outputs(items, out):
    os.makedirs(out, exist_ok=True)
    meta = {"generated": date.today().isoformat(), "count": len(items)}
    with open(os.path.join(out, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "skills": items}, f, indent=1, ensure_ascii=False)

    cats = {}
    for e in items:
        cats.setdefault(e["category"], []).append(e)
    lines = [
        "# Skills Catalog",
        "",
        f"{len(items)} skills and commands installed on this machine, generated {meta['generated']}.",
        "Type the **Invoke** value in Claude Code, or ask `/skill-finder <your goal>`.",
        "",
        "| Category | Count |",
        "|---|---|",
    ]
    for c, es in cats.items():
        anchor = re.sub(r"[^a-z0-9 -]", "", c.lower()).replace(" ", "-")
        lines.append(f"| [{c}](#{anchor}) | {len(es)} |")
    for c, es in cats.items():
        lines += ["", f"## {c}", "", "| Invoke | Use this when | Source | Path |", "|---|---|---|---|"]
        for e in es:
            lines.append(f"| `{e['invoke']}` | {md_cell(e['use_when'])} | {e['source']} | `{md_cell(e['path'])}` |")
    with open(os.path.join(out, "CATALOG.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return cats


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=here, help="folder for catalog.json and CATALOG.md (default: the skill folder)")
    ap.add_argument("--project", action="append", default=[], help="project folder whose .claude/skills to include (repeatable; default: current folder)")
    args = ap.parse_args()
    items = scan(args.project or [os.getcwd()])
    cats = write_outputs(items, args.out)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{len(items)} skills -> {os.path.join(args.out, 'CATALOG.md')}")
    for c, es in cats.items():
        print(f"  {len(es):4}  {c}")


if __name__ == "__main__":
    main()
