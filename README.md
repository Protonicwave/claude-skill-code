# claude-skill-code

A Claude Code skill, `engineer`, for writing production-quality code: plan first, build in tested phases, commit cleanly.

## What it does

- Small, obvious changes go straight to test, fix, check and commit.
- Anything larger gets a plan in `.plans/`, approved once, then built in phases. Each phase ends with the full suite, linter and type-checker passing and a real commit.
- Plans are listed in `.git/info/exclude`, so they never reach the repository and no `.gitignore` entry is needed.
- Over-building is caught in three places: the plan names a caller for every new piece, complexity and dead-code linters fail the build, and a fresh subagent reviews the branch diff before the pull request.
- The reviewer also flags any passage it had to read twice, and each finding is settled by a change and a test run where one can settle it, and put to the user where it cannot.
- A task with a time, memory or query budget states it in the plan with the input size, commits a script that measures it, and reruns that script before each commit that touches the measured code. The language references list the traps that change complexity class.
- The plan names its critical modules, and each needs full line and branch coverage before a commit that touches it. Lines that need no test are excluded with a pragma that states why.
- `engineer/scripts/check_diff.py` flags em dashes, emoji, tool attribution, plan references and US spellings in staged changes, commit messages, commit ranges or a single file. The skill installs it as local pre-commit and commit-msg hooks, so an offending change or message blocks the commit. An en dash between two digits is a range, so it is a warning rather than an error.

## Layout

- `engineer/SKILL.md`: the workflow and the self-review checklist.
- `engineer/references/`: standards, the plan template, git conventions, and one file per language: Python, TypeScript, C, C++, Rust, Go, Java, C#, shell and SQL. Each language file leads with the commands that fail the build: linter, type or analyser checks, dead code, dependency audit and coverage. Every command in them was run once on a small project, passing when clean and failing on a planted finding. Loaded only when a step needs them.
- `engineer/scripts/check_diff.py`: the style checker. Standard library only, Python 3.12 or later.
- `tests/`: pytest tests for both scripts. `pyproject.toml` holds the tool configuration only.

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

Then make every session in a git repository load it, by adding a SessionStart hook to `~/.claude/settings.json` (use `python3` where `python` is not Python 3):

```json
"hooks": {
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python \"<home>/.claude/skills/engineer/scripts/session_start.py\"",
          "timeout": 10
        }
      ]
    }
  ]
}
```

The hook runs on startup, resume, clear and compaction. Inside a git repository it tells Claude to load the skill before changing any file. Outside one it prints nothing. It points at the skill rather than containing it, because Claude Code truncates hook context at about 2 KB.

## Use

With the hook installed, the skill loads on its own in any repository. Type `/engineer` to continue a planned task in a new chat.

```sh
python engineer/scripts/check_diff.py               # staged changes
python engineer/scripts/check_diff.py main..HEAD    # a branch, including commit messages
python engineer/scripts/check_diff.py --file pr.md  # a single file
python engineer/scripts/check_diff.py --commit-msg .git/COMMIT_EDITMSG  # a commit message
```

## Test

Install the pinned tools with pip 25.1 or later, then run the checks:

```sh
python -m pip install --group dev
python -m pytest -q
python -m ruff check . && python -m ruff format --check .
python -m mypy engineer/scripts tests
python -m vulture engineer/scripts --min-confidence 80
python -m coverage run --branch --source=engineer/scripts -m pytest -q
python -m coverage report --show-missing --fail-under=100 --include=engineer/scripts/check_diff.py
```
