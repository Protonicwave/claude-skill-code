# Shell

Follow the repository's existing tooling. The defaults below are for new scripts or where the repository has none. They cover Bash. A POSIX `sh` script gets the same tools: ShellCheck and shfmt read its `#!/bin/sh` shebang and check it as POSIX.

## Detect

`*.sh` and `*.bash` files, `*.bats` tests, and files whose first line is a shell shebang. Lint settings live in `.shellcheckrc`.

## When to use it

Shell suits small utilities and wrapper scripts. Google's style guide sets the limit at 100 lines or any non-straightforward control flow, and says to use another language if performance matters. Past that, propose rewriting the script in the project's main language.

## Tooling defaults for new scripts

- Start every Bash script with:

  ```bash
  #!/bin/bash
  set -euo pipefail
  ```

  `-e` exits on a failing command, but not on one tested by `if` or `while` or followed by `&&` or `||`, and not anywhere inside a function called from such a test. Check a command whose failure matters explicitly. `-u` makes an unset variable an error. `pipefail` makes a pipeline fail when any command in it fails, not only the last; POSIX added it in the 2024 edition, so an older `sh` may not have it.
- ShellCheck at its strictest, in `.shellcheckrc`:

  ```
  enable=all
  ```

  `enable=all` turns on the optional checks too, such as `[[ ]]` in place of `[ ]` and `set -e` being suppressed in a function. Before each commit, `shellcheck <scripts>`. It exits 1 on any finding, including an unused variable (SC2034) and an unquoted expansion (SC2086), and 2 to 4 when it could not run.
- Formatting: `shfmt -i 2 -ci -bn -d <scripts>`, Google's style. It prints a diff and fails when a file is not formatted. shfmt parses a `.sh` file as POSIX unless its shebang says Bash.
- Dead code: SC2034 finds unused variables. Nothing finds an unused function, so search for callers of each function the diff adds, as `standards.md` says.

## Idiom

- Double-quote every expansion and brace every variable name: `"${var}"`, `"$(command)"`, `"${array[@]}"`. Unquoted, the value is split on whitespace and expanded as a glob. `enable=all` turns on the brace check (SC2250); `"$@"` and the other special parameters are exempt.
- Assign a command substitution to a variable before passing it as an argument. Inline, its exit status is lost even under `set -e`, and `enable=all` flags it (SC2312).
- `$(command)`, never backticks. `[[ ]]` in Bash, which does no word splitting or glob expansion inside.
- Put argument lists, especially command-line flags, in arrays: `"${args[@]}"` passes each element as one word. Under `set -u`, Bash before 4.4 stops with "unbound variable" when the array is empty; a script that must run there writes `${args[@]+"${args[@]}"}`.
- Declare function variables with `local`. A script long enough to hold another function puts its main program in a `main` function at the bottom, called as `main "$@"`.
- `read -r`, so a backslash is data and not an escape.
- Create temporary files and directories with `mktemp` and remove them from an `EXIT` trap, which runs when the shell exits, `exit` included:

  ```bash
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir}"' EXIT
  ```

## Tests

- bats-core, with tests in `*.bats` files under `test/`. Run `bats -r test`; it exits 1 if any test fails. A test calls the script through `run` and asserts on `$status` and `$output`.
- Coverage of critical scripts with kcov, on Linux or macOS. It runs the suite, follows each Bash script the tests start, and passes on the suite's exit status:

  ```sh
  kcov --include-path=<critical script> coverage bats -r test
  python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))["percent_covered"] != "100.00")' coverage/bats/coverage.json
  ```

  kcov measures lines, not branches, and has no threshold of its own, so the second line is the gate. The fallback in `standards.md` applies: full line coverage plus a test for each outcome of every condition.

## .gitignore for new projects

```
coverage/
```
