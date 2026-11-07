# claude-skill-code

A Claude Code skill, `engineer`, for writing production-quality code: plan first, build in tested phases, commit cleanly.

## What it does

- Small, obvious changes go straight to test, fix, check and commit.
- Anything larger gets a plan in `.plans/`, approved once, then built in phases. Each phase ends with the full suite, linter and type-checker passing and a real commit.
- Plans are listed in `.git/info/exclude`, so they never reach the repository and no `.gitignore` entry is needed.
- Over-building is caught in three places: the plan names a caller for every new piece, complexity and dead-code linters fail the build, and a fresh subagent reviews the branch diff before the pull request.
- `engineer/scripts/check_diff.py` flags em dashes, emoji, tool attribution, plan references and US spellings in staged changes, commit ranges or a single file.

## Layout

- `engineer/SKILL.md`: the workflow and the self-review checklist.
- `engineer/references/`: standards, language rules (Python, TypeScript), the plan template and git conventions. Loaded only when a step needs them.
- `engineer/scripts/check_diff.py`: the style checker. Standard library only, Python 3.12 or later.

## Install

Link the skill into the personal skills directory so edits here take effect immediately.

Windows (PowerShell):

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\engineer" -Target "$PWD\engineer"
```

macOS or Linux:

```sh
ln -s "$PWD/engineer" ~/.claude/skills/engineer
```

## Use

Claude picks the skill up on coding requests. Type `/engineer` to force it, or to continue a planned task in a new chat.

```sh
python engineer/scripts/check_diff.py               # staged changes
python engineer/scripts/check_diff.py main..HEAD    # a branch, including commit messages
python engineer/scripts/check_diff.py --file pr.md  # a single file
```
