---
name: skill-finder
description: Tells you exactly which installed skill or slash command to use for a goal, with the /name to type and where it lives. Use when the user asks "which skill should I use for X", "is there a skill for X", "what's the right command for X", "list my SEO/video/sales skills", "show my skill categories", "refresh the skill catalog", or types /skill-finder. Covers every installed source (user skills, plugins, desktop-app plugins, built-ins). Not for finding new skills to install from the internet (that is /find-skills).
---

# Skill finder

Picks the right skill from the ones already installed on this machine.
The catalog lives next to this file: `catalog.json` (data) and `CATALOG.md` (readable, grouped by category).

## Menu (no goal given)

If the user typed `/skill-finder` with nothing after it, or asked to "show the menu / categories", show the clickable menu:

1. Run `python ~/.claude/skills/skill-finder/scripts/menu.py` and pass its output **verbatim** as `widget_code` to the `show_widget` tool (title `skill_finder_menu`). Don't edit or retype it. If `show_widget` isn't available, print the category list from `find_skill.py --categories` instead.
2. Say one short line under it ("Pick a category, or type what you want to do.") and stop.

If the message is `/skill-finder category: <name>`:

1. Run `python ~/.claude/skills/skill-finder/scripts/menu.py --category "<name>"` and pass its output verbatim to `show_widget` (title `skill_finder_<category>` in snake_case).
2. One short line under it, then stop.

Clicking a skill in the menu sends "Run the /name skill…". Then invoke that skill with the Skill tool.

## Steps (goal given)

1. **Search.** Run the finder with the user's goal in their own words:
   ```bash
   python ~/.claude/skills/skill-finder/scripts/find_skill.py "<goal>"
   ```
   - Category list: `--categories`. Everything in one category: `--category "SEO"`.
   - More results: `--top 15`.
2. **Pick.** Read the top results. Choose the best 1 (at most 3) using the `use when` line and the description. Prefer:
   - the user's own skills (`Mebarez (own)`, source `user`) when they fit the job,
   - a specific skill over a general one (e.g. `/remotion-captions` over `/remotion-best-practices` for captions),
   - a skill over a plugin command that only wraps it.
   If a result looks close but you're unsure, open its SKILL.md at the listed `path` and check.
3. **Answer short.** For each pick give:
   - the exact thing to type, e.g. `/seo-audit`,
   - one line on why it fits,
   - the path.
   Then offer to run it now. If nothing fits, say so and suggest `/find-skills` to look for one online.

## Refresh the catalog

When skills were added or removed, or the catalog date (printed on the first line) is old:
```bash
python ~/.claude/skills/skill-finder/scripts/build_catalog.py
```
It rescans every source and rewrites `catalog.json` and `CATALOG.md` in this folder. Add `--project <folder>` to include that project's `.claude/skills` (the current folder is included by default).

## Example

User: "which skill do I use to make a vertical promo video with captions?"
→ run `find_skill.py "vertical promo video with captions"`, then answer:
- `/hyperframes` — HTML-to-video, holds the render rules for vertical clips and captions. `~/.claude/skills/hyperframes/SKILL.md`
- `/remotion-captions` — if the project is already in Remotion.
