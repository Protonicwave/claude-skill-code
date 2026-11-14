# Python

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`pyproject.toml`, `requirements*.txt`, `setup.cfg`, `uv.lock`, `poetry.lock`. The lock file tells you the package manager: use that one.

## Tooling defaults for new projects

- Python 3.12 or later, declared in `requires-python`.
- `pyproject.toml` as the single config file. `uv` if installed, otherwise `venv` and `pip`.
- Ruff for linting and formatting:

  ```toml
  [tool.ruff.lint]
  select = ["E", "F", "W", "I", "B", "UP", "SIM", "RUF", "S", "PT", "N", "C90", "PLR"]

  [tool.ruff.lint.mccabe]
  max-complexity = 10

  [tool.ruff.lint.per-file-ignores]
  # pytest's assertion rewriting relies on bare assert, and test tables use literal values.
  "tests/**" = ["S101", "PLR2004"]
  ```

  `C90` and `PLR` turn over-built code into lint failures: too many branches, arguments, returns or statements in one function. Treat a failure as a design signal and restructure, rather than raising the limit.

  `S` is flake8-bandit's security rules: shell calls, SQL built from strings, hard-coded passwords. It is the security scanner, so it stays in `select`.

- Vulture (`vulture src --min-confidence 80`) before each commit, to catch functions, classes and variables nothing calls. Ruff only finds unused imports and locals.
- pip-audit for the dependency audit: `pip-audit .` for a project declared in `pyproject.toml`, `pip-audit -r requirements.txt` for a requirements file. It exits 1 on any known vulnerability. It reads `pyproject.toml` and `pylock.*.toml`, not `uv.lock` or `poetry.lock`.
- mypy with `strict = true`, or pyright in strict mode if the repository uses it.
- pytest. Tests live in `tests/`, mirroring the package layout.
- `src/` layout for anything that will be installed or imported by other code.

## Types

- Annotate every function signature. No implicit `Any`. Explicit `Any` only at a boundary, with a comment.
- `@dataclass(frozen=True, slots=True)` for value objects.
- `Enum` or `Literal` for closed sets. `NewType` for identifiers that must not be mixed up.
- Parse external data into typed objects at the boundary. Use the standard library unless validation is heavy enough to justify a dependency, or the repository already uses pydantic.
- `typing.assert_never` in the final branch of exhaustive `match` statements.

## Errors

- Raise specific built-in exceptions where they fit (`ValueError`, `KeyError`, `LookupError`). Define a domain exception only when a caller needs to catch it specifically.
- `raise NewError(...) from err` when wrapping, to keep the cause.
- No bare `except:`. No `except Exception` except at the process boundary.
- `assert` only for internal invariants that indicate a bug. Never for validating input, because `python -O` strips assertions.

## Resources and I/O

- `with` for every file, lock, connection and session.
- Every network call has a timeout. `requests` and `httpx` have no safe default: pass `timeout=` explicitly.
- `pathlib.Path` for paths. Pass `encoding="utf-8"` to every text-mode open: the default varies by platform.
- Generators or iterators for data whose size you do not control.
- `subprocess.run([...], check=True)` with an argument list. Never `shell=True` with interpolated input.

## Idiom

- No mutable default arguments.
- Comprehensions for simple transforms. A loop once the logic needs more than one condition.
- `logging.getLogger(__name__)` in modules, with `%`-style arguments so formatting is lazy. No `print` outside CLI output.
- Absolute imports. No wildcard imports. No import-time side effects beyond defining things.
- Constants in `UPPER_SNAKE_CASE` at module top, with units in the name.

## Performance

Traps that change the complexity class or grow without bound, each documented CPython behaviour:

- `x in some_list` inside a loop scans the list every time. Build a `set` or `dict` once: lookups take constant time on average.
- `list.pop(0)` and `list.insert(0, x)` move every element. Use `collections.deque` for a queue.
- `+=` on a `str` or `bytes` in a loop is quadratic in the total length. Append the pieces to a list and `"".join` them once.
- Range and nearest-value lookups over sorted data: `bisect` on a sorted list of boundaries, O(log n). `insort` is still O(n) per insertion, so load everything and sort once rather than inserting items one by one.
- `functools.cache` and `lru_cache(maxsize=None)` grow without bound. A cache keyed on external input gets an explicit `maxsize`.

To compare two implementations, use `timeit.repeat` and take the minimum: higher readings come from other processes, not from the code.

## Tests

- Plain `assert` with pytest's rewriting.
- `@pytest.mark.parametrize` for edge-case tables.
- `tmp_path` for filesystem tests and `monkeypatch` for environment and clock. Do not patch internal functions.
- Commands: `pytest`, `ruff check .`, `ruff format --check .`, `mypy .` unless the repository says otherwise.
- Coverage of critical modules: `coverage run --branch --source=<package> -m pytest`, then `coverage report --show-missing --fail-under=100 --include=<paths>`. Without `--source`, a critical module no test imports is left out of the report and the check passes. If the repository already uses pytest-cov, run `pytest --cov=<package> --cov-branch` and the same `coverage report`. Exclude a line with `# pragma: no cover: <reason>`, or a branch that cannot be taken with `# pragma: no branch: <reason>`. A repository that sets `exclude_lines` replaces the default pragma; add patterns with `exclude_also` instead.

## .gitignore for new projects

```
__pycache__/
*.py[cod]
.venv/
build/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
```
