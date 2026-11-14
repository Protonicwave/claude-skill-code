from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty git repository that is also the working directory."""
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    for key, value in {
        "user.name": "Test",
        "user.email": "test@example.com",
        "commit.gpgsign": "false",
        "core.autocrlf": "false",
    }.items():
        git(path, "config", key, value)
    monkeypatch.chdir(path)
    return path
