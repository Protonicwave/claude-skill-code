from __future__ import annotations

from pathlib import Path

import pytest

from git_command import git


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
