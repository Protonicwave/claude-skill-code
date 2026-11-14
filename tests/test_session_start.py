from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

import session_start


def run_hook(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: str
) -> str:
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    assert session_start.main() == 0
    return capsys.readouterr().out


@pytest.mark.parametrize("directory_name", ["plain", "missing"])
def test_prints_nothing_outside_a_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    directory_name: str,
) -> None:
    # Stops git from finding a repository above the temporary directory.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    (tmp_path / "plain").mkdir()
    payload = json.dumps({"cwd": str(tmp_path / directory_name)})

    assert run_hook(monkeypatch, capsys, payload) == ""


def test_points_at_the_skill_inside_a_repository(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    out = run_hook(monkeypatch, capsys, json.dumps({"cwd": str(repo)}))

    output = json.loads(out)["hookSpecificOutput"]
    assert output["hookEventName"] == "SessionStart"
    assert "load the skill with the Skill tool (name: engineer)" in output["additionalContext"]
    assert "SKILL.md" in output["additionalContext"]


@pytest.mark.parametrize("payload", ["", "{}"], ids=["run by hand", "no cwd"])
def test_falls_back_to_the_working_directory(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: str
) -> None:
    out = run_hook(monkeypatch, capsys, payload)

    assert json.loads(out)["hookSpecificOutput"]["hookEventName"] == "SessionStart"
