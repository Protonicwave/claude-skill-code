"""Tell a Claude Code session that starts inside a git repository to use the engineer skill.

Runs as a SessionStart hook. Reads the hook payload from stdin and prints a
short instruction as additional context, or prints nothing when the session is
not in a repository, so sessions that are not about code stay clean.

The instruction points at the skill rather than containing it: Claude Code
truncates hook context at about 2 KB, and one copy of the skill is easier to
keep correct than two.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
GIT_TIMEOUT_SECONDS = 5


def session_directory(payload: str) -> Path:
    # An empty payload means the script was run by hand rather than by the hook.
    if not payload.strip():
        return Path.cwd()
    cwd = json.loads(payload).get("cwd")
    return Path(cwd) if cwd else Path.cwd()


def is_git_work_tree(directory: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT_SECONDS,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def session_context() -> str:
    skill_file = (SKILL_DIR / "SKILL.md").as_posix()
    return (
        "This session started inside a git repository, so the engineer skill governs "
        "every code change here. Before you create, edit or delete any file in this "
        "repository, load the skill with the Skill tool (name: engineer) and follow it "
        f"from its first step. If the Skill tool is unavailable, read {skill_file} instead. "
        "Load it once per session; after the conversation is compacted, load it again. "
        "It does not apply to questions that change no files."
    )


def main() -> int:
    if not is_git_work_tree(session_directory(sys.stdin.read())):
        return 0
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": session_context(),
        }
    }
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
