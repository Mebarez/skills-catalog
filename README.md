# skills-catalog

Typing `/` in Claude Code can show hundreds of skills in no order. This repo:

1. **Scans** every skill source on your machine and reads each `SKILL.md` (name, description, path).
2. **Sorts** them into clear categories (Video & Motion, SEO, Social, Sales, Dev, Docs/PDF, Design…) in `CATALOG.md` and `catalog.json`.
3. Ships **`/skill-finder`**, a skill that tells you which one to use for a goal, the exact `/name` to type, and where it lives.

Python 3.8+ only, no packages to install. Works on Windows, macOS and Linux.

## Install

```bash
git clone https://github.com/<you>/skills-catalog.git
cd skills-catalog
python install.py
```

That copies `skill-finder/` to `~/.claude/skills/skill-finder` and builds the catalog there. Start a new Claude Code session so the skill shows up.

## Use

In Claude Code, type `/skill-finder` on its own to open a **clickable menu**: pick a category, see its skills, and click one to run it. The menu has a search box too. It shows in apps that render inline widgets, such as the Claude desktop app; anywhere else you get a text list.

Or ask with a goal:

```
/skill-finder make a vertical promo video with captions
/skill-finder which skill audits my site's SEO?
/skill-finder show my categories
```

From a terminal:

```bash
python ~/.claude/skills/skill-finder/scripts/find_skill.py "review my python code"
python ~/.claude/skills/skill-finder/scripts/find_skill.py --categories
python ~/.claude/skills/skill-finder/scripts/find_skill.py --category "SEO"
```

Rebuild after installing or removing skills:

```bash
python ~/.claude/skills/skill-finder/scripts/build_catalog.py
```

Rebuild the copy in this repo (the one you browse on GitHub):

```bash
python skill-finder/scripts/build_catalog.py --out .
```

## What gets scanned

| Source | Where | Typed as |
|---|---|---|
| Project skills | `<project>/.claude/skills/*/SKILL.md` | `/name` |
| User skills | `~/.claude/skills/*/SKILL.md` | `/name` |
| CLI plugins | `~/.claude/plugins/installed_plugins.json` → `skills/` and `commands/` | `/plugin:name` |
| Desktop-app plugins | `%LOCALAPPDATA%/Claude-Data/*/rpm/*/*/plugin_*` | `/plugin:name` |
| Anthropic skills | `%LOCALAPPDATA%/Claude-Data/*/local-agent-mode-sessions/skills-plugin/*/*/skills` | `/anthropic-skills:name` |
| Built-ins | listed in `build_catalog.py` (`BUILTINS`) | `/name` |

Other locations: set `CLAUDE_DATA_DIRS` (separated by `;` on Windows, `:` elsewhere) to extra desktop-app data folders.

## Change the categories

Edit `skill-finder/scripts/build_catalog.py`:

- `CATEGORIES` — ordered rules (plugin name, name regex). First match wins.
- `OVERRIDES` — pin a specific skill to a category.

Then rebuild. Anything that matches nothing lands in **Other**, so check that section after adding skills.

## Files

```
skill-finder/SKILL.md                  the /skill-finder skill
skill-finder/scripts/build_catalog.py  scanner + categorizer
skill-finder/scripts/find_skill.py     ranks skills for a goal
skill-finder/scripts/menu.py           HTML for the clickable category menu
install.py                             copies the skill to ~/.claude/skills and builds the catalog
CATALOG.md, catalog.json               example catalog from the author's machine
```

## License

MIT
