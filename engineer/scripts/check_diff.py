"""Flag text that breaks the house style in added lines, commit messages or a file.

Usage:
    check_diff.py                 staged changes (git diff --cached)
    check_diff.py <base>..HEAD    a commit range, including its commit messages
    check_diff.py --file <path>   a single text file, such as a pull request body
    check_diff.py --commit-msg <path>
                                  a commit message file, as a commit-msg hook passes it

Exits 1 if any error is found. Warnings need judgement: an identifier that
mirrors an external interface keeps its spelling, for example.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Iterable, Iterator
from io import TextIOWrapper
from pathlib import Path
from typing import cast

# Whole Unicode blocks rather than the emoji property, which re cannot match. Two
# of the blocks also hold symbols that are not emoji, such as a check mark or a
# sharp sign; flagging those is the price of missing no emoji in them.
# U+FE0F requests emoji presentation, so it catches emoji built on any other base.
EMOJI_CLASS = (
    "["
    "\U0001f000-\U0001faff"  # supplementary emoji blocks, flags included
    "\U00002600-\U000027bf"  # Miscellaneous Symbols and Dingbats
    "\U0000231a\U0000231b\U000023e9-\U000023fa"  # watch, hourglass, media controls
    "\U000025fd\U000025fe"  # medium small squares
    "\U00002b1b\U00002b1c\U00002b50-\U00002b55"  # large squares, stars and circles
    "\U0000fe0f"  # variation selector 16
    "]"
)

ERROR_PATTERNS: dict[str, re.Pattern[str]] = {
    # An en dash between two digits is a range, not punctuation: a warning instead.
    "em or en dash": re.compile(r"\N{EM DASH}|(?<!\d)\N{EN DASH}|\N{EN DASH}(?!\d)"),
    "tool attribution": re.compile(r"co-authored-by|generated (with|by) ", re.IGNORECASE),
    "plan reference": re.compile(r"\.plans/|implementation plan|as per (the )?plan", re.IGNORECASE),
    "emoji": re.compile(EMOJI_CLASS),
}

# Warnings, not errors: each can be legitimate (an app that calls the Anthropic
# API, a three-phase power model, CSS `color`), so a human judges them.
WARNING_PATTERNS: dict[str, re.Pattern[str]] = {
    "en dash in a numeric range": re.compile(r"\d\N{EN DASH}\d"),
    "assistant name": re.compile(r"\b(claude|anthropic|chatgpt|copilot)\b", re.IGNORECASE),
    "possible plan reference": re.compile(r"\bphase \d", re.IGNORECASE),
    "US spelling": re.compile(
        r"(organiz|initializ|optimiz|serializ|normaliz|analyz|recogniz|customiz|authoriz"
        r"|summariz|synchroniz|prioritiz|finaliz|utiliz|minimiz|maximiz|categoriz"
        r"|standardiz|sanitiz|tokeniz|visualiz|memoiz|color|behavior|favor(?!ite)"
        r"|honor|neighbor|labor(?!at)|center|canceled|canceling|labeled|labeling"
        r"|modeled|modeling|traveled|catalog(?!ue)|defense|gray)",
        re.IGNORECASE,
    ),
}

MAX_FINDINGS_SHOWN = 200
SCISSORS_LINE = "# ------------------------ >8 ------------------------"


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout


def added_lines(diff: str) -> Iterator[tuple[str, str]]:
    """Yield (location, text) for each line the diff adds."""
    path = "?"
    line_number = 0
    # Header lines are only recognised between "diff --git" and the first hunk,
    # so an added line whose content begins with "++" is not mistaken for one.
    in_header = False
    for raw in diff.splitlines():
        if raw.startswith("diff --git"):
            in_header = True
        elif in_header and raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else raw[4:]
        elif raw.startswith("@@"):
            in_header = False
            match = re.search(r"\+(\d+)", raw)
            line_number = int(match.group(1)) if match else 0
        elif in_header or raw.startswith("\\"):
            continue
        elif raw.startswith("+"):
            yield f"{path}:{line_number}", raw[1:]
            line_number += 1
        elif not raw.startswith("-"):
            line_number += 1


def commit_message_lines(revision_range: str) -> Iterator[tuple[str, str]]:
    log = run_git("log", "--format=%h%x00%B%x01", revision_range)
    for entry in log.split("\x01"):
        if "\x00" not in entry:
            continue
        short_hash, message = entry.strip().split("\x00", 1)
        for offset, text in enumerate(message.splitlines(), start=1):
            yield f"commit {short_hash} line {offset}", text


def file_lines(path: Path) -> Iterator[tuple[str, str]]:
    for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        yield f"{path}:{number}", text


def commit_message_file_lines(path: Path) -> Iterator[tuple[str, str]]:
    """Yield the lines of a message file that git records in the commit.

    Git drops lines starting with "#" and, under `commit --verbose`, everything
    from the scissors line down. Only the default comment character is handled.
    """
    for location, text in file_lines(path):
        if text == SCISSORS_LINE:
            return
        if not text.startswith("#"):
            yield location, text


def scan(lines: Iterable[tuple[str, str]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for location, text in lines:
        for label, pattern in ERROR_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{location}: {label}: {text.strip()}")
        for label, pattern in WARNING_PATTERNS.items():
            match = pattern.search(text)
            if match:
                warnings.append(f"{location}: {label} '{match.group(0)}': {text.strip()}")
    return errors, warnings


def collect(argv: list[str]) -> Iterator[tuple[str, str]]:
    match argv:
        case []:
            yield from added_lines(run_git("diff", "--cached", "--no-color"))
        case ["--file", path]:
            yield from file_lines(Path(path))
        case ["--commit-msg", path]:
            yield from commit_message_file_lines(Path(path))
        case [revision_range] if ".." in revision_range:
            yield from added_lines(run_git("diff", "--no-color", revision_range))
            yield from commit_message_lines(revision_range)
        case _:
            raise SystemExit(
                "expected no arguments, '<base>..HEAD', '--file <path>' or "
                f"'--commit-msg <path>', got {argv}"
            )


def report(title: str, findings: list[str]) -> None:
    if not findings:
        return
    print(f"{title} ({len(findings)}):")
    for finding in findings[:MAX_FINDINGS_SHOWN]:
        print(f"  {finding}")
    if len(findings) > MAX_FINDINGS_SHOWN:
        print(f"  ... {len(findings) - MAX_FINDINGS_SHOWN} more")


def main(argv: list[str]) -> int:
    errors, warnings = scan(collect(argv))
    report("Errors", errors)
    report("Warnings: judge each one", warnings)
    if not errors and not warnings:
        print("Clean.")
    return 1 if errors else 0


if __name__ == "__main__":  # pragma: no cover: entry point that only wires tested parts
    cast(TextIOWrapper, sys.stdout).reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
