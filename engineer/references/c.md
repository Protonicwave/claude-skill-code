# C

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`CMakeLists.txt`, `meson.build` or `Makefile` names the build. `compile_commands.json` is what clang-tidy reads, through `-p <build directory>`, to see the real compiler flags.

## Tooling defaults for new projects

- GCC or Clang warnings, all of them errors:

  ```sh
  -std=c17 -Wall -Wextra -Wpedantic -Wshadow -Wformat=2 -Wcast-qual -Wnull-dereference -Werror
  ```

  `-Wextra` adds to `-Wall` rather than replacing it. `-Wnull-dereference` is only active when optimisation is on, so an `-O0` build reports nothing for it.

- clang-tidy, configured in `.clang-tidy` at the repository root:

  ```yaml
  Checks: '-*,clang-diagnostic-*,bugprone-*,cert-*,clang-analyzer-*,misc-*,readability-function-cognitive-complexity,readability-function-size'
  WarningsAsErrors: '*'
  CheckOptions:
    readability-function-cognitive-complexity.Threshold: 15
    readability-function-size.LineThreshold: 60
  ```

  `clang-diagnostic-*` keeps the compiler's own warnings: without it, `-*` turns them off and the `-W` flags report nothing. `cert-*` holds the security checks; `clang-analyzer-*` adds path-sensitive checks such as null dereference. The two `readability-` checks are the complexity limits, review aids as `standards.md` describes; left at their defaults, cognitive complexity 25 and 800 statements, they never fire on ordinary code.

  Run it with `clang-tidy -quiet -p <build directory> src/*.c` where the build writes `compile_commands.json`, so it sees the real flags. Without one, give the warning flags above after `--`, which also tells clang-tidy to ignore any compilation database: `clang-tidy -quiet src/*.c -- <warning flags>`.

- cppcheck as the dead-code check. `unusedFunction` needs the whole program in one run, so give it the source tree, never one file at a time. Without `--error-exitcode` it exits 0 whatever it finds:

  ```sh
  cppcheck -q --enable=warning,style,performance,portability,unusedFunction --error-exitcode=1 src
  ```

- There is no dependency audit command for C. OSV-Scanner reads `conan.lock`, but it holds no ConanCenter advisories for common libraries and passed a lock pinning zlib 1.2.11, so it is not a gate here. When a change adds or upgrades a vendored or package-managed library, say in the report and the pull request that it was not audited, and name the library and its version.

## Types

- Unsigned arithmetic wraps silently: bound every unsigned operation that can exceed its type (CERT INT30-C).
- Signed overflow is undefined behaviour, not wrapping. Check the operands before the operation (CERT INT32-C); UndefinedBehaviorSanitizer reports it at run time.
- Every conversion, implicit or cast, must keep the value (CERT INT31-C). Check the range before narrowing or changing signedness.

## Errors

- Check the return value of every standard library call that can fail: `malloc`, `fopen`, `fread`, `snprintf`, `strtol` and the rest (CERT ERR33-C).

## Resources and I/O

- Every allocation is matched by exactly one `free` of the same pointer (CERT MEM31-C), and nothing reads memory after it is freed (CERT MEM30-C). AddressSanitizer reports use-after-free and double free at run time.
- The test suite also runs under the sanitisers, in a separate build and CI job from the release build. AddressSanitizer slows a program about 2x.

  ```sh
  -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer
  ```

  `-fno-sanitize-recover=all` makes UndefinedBehaviorSanitizer exit non-zero on its first report instead of printing and carrying on.
- Code that uses threads also runs its tests under ThreadSanitizer, in a third build: it cannot be combined with AddressSanitizer in one program. Every object linked in must be compiled with it. It costs about 5x to 15x in time and 5x to 10x in memory, and exits with status 66 on a report.

  ```sh
  -g -O1 -fsanitize=thread
  ```

## Tests

- Build the tests with `--coverage` on both the compile and the link line. It is shorthand for `-fprofile-arcs -ftest-coverage` when compiling and `-lgcov` when linking.
- Check a critical module with gcovr after the tests run. It exits non-zero when either figure is below its threshold, and `--filter` keeps the report to the named file:

  ```sh
  gcovr --root . --filter src/<module>.c --fail-under-line 100 --fail-under-branch 100 <build directory>
  ```

## .gitignore for new projects

```
build/
*.o
*.gcda
*.gcno
```
