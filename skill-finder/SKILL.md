---
name: skill-finder
description: Tells you exactly which installed skill or slash command to use for a goal, with the /name to type and where it lives. Use when the user asks "which skill should I use for X", "is there a skill for X", "what's the right command for X", "list my SEO/video/sales skills", "show my skill categories", "refresh the skill catalog", or types /skill-finder. Covers every installed source (user skills, plugins, desktop-app plugins, built-ins). Not for finding new skills to install from the internet (that is /find-skills).
---

# Skill finder

Picks the right skill from the ones already installed on this machine.
The catalog lives next to this file: `catalog.json` (data) and `CATALOG.md` (readable, grouped by category).

## Steps

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
