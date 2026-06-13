# Installing agentic-research

These are **agent skills** — Markdown instruction files an AI coding agent reads to gain a capability. They work with any harness that loads skills from a directory.

## Requirements

- An AI agent harness that supports skills (e.g. **Claude Code**).
- **Python 3.9+** for the runnable backends (standard library only — no `pip install` needed).
- Optional: the **scite MCP** server for richer citation verification (paid; the skills work without it).

## Option A — Claude Code

Copy or symlink the `skills/` directory into your project's (or user's) skills location:

```bash
# project-level (per-repo):
cp -r skills/* /path/to/your-project/.claude/skills/

# or symlink the whole suite:
ln -s "$(pwd)/skills" /path/to/your-project/.claude/skills/agentic-research
```

On Windows (PowerShell), use a junction:

```powershell
New-Item -ItemType Junction -Path "C:\your-project\.claude\skills\agentic-research" -Target "$PWD\skills"
```

Also copy the convention into your steering/rules so the agent records AI provenance:

```bash
cp steering/ai-research-provenance.md /path/to/your-project/.claude/   # or your agent's steering dir
```

## Option B — other agents (Gemini CLI, Codex, Kiro, …)

Point the agent's skills directory at `skills/` the same way (copy or symlink/junction). The skills are written agent-agnostically; nothing here is Claude-specific.

## Option C — just read them

Every `SKILL.md` is a self-contained, human-readable methodology. You can use them as checklists and run the Python scripts directly without any agent:

```bash
python skills/acquire-corpus/scripts/search_openalex.py search --query "AI tutoring K-12" --max 50 --mailto you@example.com
python skills/dedupe-records/scripts/dedupe_records.py corpus.jsonl --report
python skills/prisma-flow/scripts/prisma_flow.py counts.json --strict
```

## Verify it works

```bash
# Should print a RETRACTED verdict for the Wakefield 1998 paper (keyless):
python skills/verify-sources/scripts/resolve_citation.py --mailto you@example.com 10.1016/S0140-6736(97)11096-0
```

## Then just ask

With the skills loaded, drive the pipeline in natural language:

- *"Design a systematic-review protocol for [topic]."* → `design-review-protocol`
- *"Build a corpus for [topic] and log the search."* → `acquire-corpus` → `dedupe-records`
- *"Screen these papers against my criteria with two reviewers."* → `screen-literature` (dual mode)
- *"Appraise the risk of bias of the included studies."* → `appraise-risk-of-bias` (will ask you to confirm)
- *"Verify every citation in this draft is real."* → `verify-sources`
- *"Generate the PRISMA flow diagram."* → `prisma-flow`

The agent selects the skill from your intent.
