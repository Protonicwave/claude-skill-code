from __future__ import annotations

import re
from pathlib import Path

import pytest

import check_diff
from conftest import git

EM_DASH = "\u2014"
EN_DASH = "\u2013"
ROCKET = "\U0001f680"


def write(path: Path, text: str) -> None:
    # Bytes, not text mode, so Windows does not turn the newlines into CRLF.
    path.write_bytes(text.encode("utf-8"))


def check_text(tmp_path: Path, text: str) -> int:
    path = tmp_path / "body.md"
    write(path, text)
    return check_diff.main(["--file", str(path)])


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", message)


def test_clean_text_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert check_text(tmp_path, "A plain sentence.\n") == 0
    assert capsys.readouterr().out == "Clean.\n"


@pytest.mark.parametrize(
    ("text", "label"),
    [
        (f"one {EM_DASH} two", "em or en dash"),
        (f"one {EN_DASH} two", "em or en dash"),
        ("Co-Authored-By: someone", "tool attribution"),
        ("Generated with a tool", "tool attribution"),
        ("see .plans/task.md", "plan reference"),
        ("as per the plan", "plan reference"),
        (f"ship it {ROCKET}", "emoji"),
    ],
)
def test_error_fails_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str, label: str
) -> None:
    assert check_text(tmp_path, text + "\n") == 1
    assert f"body.md:1: {label}: {text}" in capsys.readouterr().out


@pytest.mark.parametrize(
    "emoji",
    [
        "\N{WHITE HEAVY CHECK MARK}",
        "\N{SPARKLES}",
        "\N{WARNING SIGN}",
        "\N{WARNING SIGN}\N{VARIATION SELECTOR-16}",
        "\N{WHITE MEDIUM STAR}",
        "\N{HOURGLASS WITH FLOWING SAND}",
        "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
        "1\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}",
        "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
        "\N{WOMAN}\N{ZERO WIDTH JOINER}\N{PERSONAL COMPUTER}",
    ],
)
def test_emoji_fails_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], emoji: str
) -> None:
    assert check_text(tmp_path, f"done {emoji}\n") == 1
    assert "body.md:1: emoji: " in capsys.readouterr().out


@pytest.mark.parametrize(
    "symbol",
    [
        "\N{RIGHTWARDS ARROW}",
        "\N{MULTIPLICATION SIGN}",
        "\N{DEGREE SIGN}",
        "\N{MICRO SIGN}",
        "\N{GREEK SMALL LETTER SIGMA}",
        "\N{COPYRIGHT SIGN}",
        "\N{BLACK RIGHT-POINTING TRIANGLE}",
    ],
)
def test_symbols_used_in_technical_text_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], symbol: str
) -> None:
    assert check_text(tmp_path, f"x {symbol} y\n") == 0
    assert capsys.readouterr().out == "Clean.\n"


@pytest.mark.parametrize(
    ("text", "label"),
    [
        ("ask Claude first", "assistant name 'Claude'"),
        ("phase 2 is next", "possible plan reference 'phase 2'"),
        ("the color red", "US spelling 'color'"),
    ],
)
def test_warning_does_not_fail_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str, label: str
) -> None:
    assert check_text(tmp_path, text + "\n") == 0
    out = capsys.readouterr().out
    assert f"body.md:1: {label}: {text}" in out
    assert "Errors" not in out


@pytest.mark.parametrize("word", ["colour", "behaviour", "laboratory", "catalogue"])
def test_uk_spelling_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str], word: str) -> None:
    assert check_text(tmp_path, word + "\n") == 0
    assert capsys.readouterr().out == "Clean.\n"


def test_findings_beyond_the_display_limit_are_counted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    total = check_diff.MAX_FINDINGS_SHOWN + 1
    assert check_text(tmp_path, f"a {EM_DASH} b\n" * total) == 1
    out = capsys.readouterr().out
    assert f"Errors ({total}):" in out
    assert "  ... 1 more" in out


@pytest.mark.parametrize("argv", [["--bogus"], ["HEAD"], ["--file"]])
def test_unknown_arguments_are_rejected(argv: list[str]) -> None:
    with pytest.raises(SystemExit, match="expected no arguments"):
        check_diff.main(argv)


def test_staged_changes_report_added_lines_only(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notes = repo / "notes.txt"
    write(notes, f"a\nold {EM_DASH}\nb\n")
    commit_all(repo, "add notes")
    write(notes, f"a\nb\nnew {EM_DASH}\n")
    git(repo, "add", ".")

    assert check_diff.main([]) == 1
    out = capsys.readouterr().out
    assert f"notes.txt:3: em or en dash: new {EM_DASH}" in out
    assert "old" not in out


def test_added_line_starting_with_plus_signs_is_scanned(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo / "notes.txt", f"++ {EM_DASH}\n")
    git(repo, "add", ".")

    assert check_diff.main([]) == 1
    assert f"notes.txt:1: em or en dash: ++ {EM_DASH}" in capsys.readouterr().out


def test_missing_final_newline_marker_is_not_scanned(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo / "notes.txt", f"x {EM_DASH}")
    git(repo, "add", ".")

    assert check_diff.main([]) == 1
    assert "Errors (1):" in capsys.readouterr().out


def test_commit_range_checks_added_lines_and_commit_messages(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo / "readme.txt", "base\n")
    commit_all(repo, "add readme")
    base = git(repo, "rev-parse", "HEAD").strip()
    write(repo / "notes.txt", f"x {EM_DASH}\n")
    commit_all(repo, "add notes\n\nCo-Authored-By: someone")

    assert check_diff.main([f"{base}..HEAD"]) == 1
    out = capsys.readouterr().out
    assert "notes.txt:1: em or en dash" in out
    assert re.search(r"commit [0-9a-f]+ line 3: tool attribution: Co-Authored-By", out)
