# C++

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none. Rule numbers such as R.11 are from the C++ Core Guidelines.

## Detect

`CMakeLists.txt`, `meson.build` or `Makefile` names the build. `compile_commands.json` is what clang-tidy reads, through `-p <build directory>`, to see the real compiler flags.

## Tooling defaults for new projects

- GCC or Clang warnings, all of them errors:

  ```sh
  -std=c++20 -Wall -Wextra -Wpedantic -Wshadow -Wformat=2 -Wcast-qual -Wnull-dereference -Werror
  ```

  `-Wnull-dereference` is only active when optimisation is on, so an `-O0` build reports nothing for it.

- clang-tidy, configured in `.clang-tidy` at the repository root:

  ```yaml
  Checks: '-*,clang-diagnostic-*,bugprone-*,cert-*,clang-analyzer-*,cppcoreguidelines-*,modernize-*,misc-*,performance-*,readability-function-cognitive-complexity,readability-function-size,-modernize-use-trailing-return-type'
  WarningsAsErrors: '*'
  CheckOptions:
    readability-function-cognitive-complexity.Threshold: 15
    readability-function-size.LineThreshold: 60
  ```

  `clang-diagnostic-*` keeps the compiler's own warnings: without it, `-*` turns them off and the `-W` flags report nothing. `cppcoreguidelines-*` enforces many of the rules below, such as no owning raw pointers and no C arrays. `modernize-use-trailing-return-type` is off because it flags every function written with its return type first. The two `readability-` checks are the complexity limits, review aids as `standards.md` describes; left at their defaults, cognitive complexity 25 and 800 statements, they never fire on ordinary code.

  Run it with `clang-tidy -quiet -p <build directory> src/*.cpp` where the build writes `compile_commands.json`, so it sees the real flags. Without one, give the warning flags above after `--`, which also tells clang-tidy to ignore any compilation database: `clang-tidy -quiet src/*.cpp -- <warning flags>`.

- cppcheck as the dead-code check. `unusedFunction` needs the whole program in one run, so give it the source tree, never one file at a time. Without `--error-exitcode` it exits 0 whatever it finds:

  ```sh
  cppcheck -q --enable=warning,style,performance,portability,unusedFunction --error-exitcode=1 src
  ```

- There is no dependency audit command for C++. OSV-Scanner reads `conan.lock`, but it holds no ConanCenter advisories for common libraries and passed a lock pinning zlib 1.2.11, so it is not a gate here. When a change adds or upgrades a vendored or package-managed library, say in the report and the pull request that it was not audited, and name the library and its version.

## Types

- Interfaces are precisely and strongly typed (I.4).
- `std::array` or `std::vector`, never a C array (SL.con.1). Prefer the standard library to hand-written code (ES.1).
- Objects are `const` or `constexpr` unless they must change (ES.25).

## Errors

- State each function's preconditions (I.5).
- `noexcept` where leaving the function by an exception is impossible or unacceptable (E.12).
- RAII keeps error paths from leaking (E.6). Never throw while directly owning an object (E.13).

## Resources and I/O

- Every resource is managed by a handle that releases it in its destructor (R.1).
- No explicit `new` and `delete` (R.11), and no `malloc` and `free` (R.10). The result of any explicit allocation goes straight to a managing object (R.12).
- `std::unique_ptr` holds an owning pointer (ES.24). A raw pointer `T*` never owns (R.3).
- The test suite also runs under the sanitisers, in a separate build and CI job from the release build. AddressSanitizer slows a program about 2x.

  ```sh
  -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer
  ```

  `-fno-sanitize-recover=all` makes UndefinedBehaviorSanitizer exit non-zero on its first report instead of printing and carrying on.
- Code that uses threads also runs its tests under ThreadSanitizer, in a third build: it cannot be combined with AddressSanitizer in one program. Every object linked in must be compiled with it. It costs about 5x to 15x in time and 5x to 10x in memory, and exits with status 66 on a report.

  ```sh
  -g -O1 -fsanitize=thread
  ```

## Idiom

- Define no copy, move or destructor operations if you can avoid it (C.20). If you define or delete any of them, define or delete them all (C.21).
- Keep scopes small (ES.5).
- Assume the code will run in a multi-threaded program (CP.1). Avoid data races (CP.2) by sharing as little writable data as possible (CP.3).

## Performance

- Minimise the number of allocations and deallocations (Per.14).

## Tests

- Build the tests with `--coverage` on both the compile and the link line. It is shorthand for `-fprofile-arcs -ftest-coverage` when compiling and `-lgcov` when linking.
- Check a critical module with gcovr after the tests run. It exits non-zero when either figure is below its threshold, and `--filter` keeps the report to the named file:

  ```sh
  gcovr --root . --filter src/<module>.cpp --exclude-throw-branches --exclude-unreachable-branches --exclude-noncode-lines --fail-under-line 100 --fail-under-branch 100 <build directory>
  ```

  The three exclusions remove what the compiler generates for exceptions. Without them a fully tested function that calls `push_back` stays below 100%: the branch to the throw is never taken, and the closing brace runs only when unwinding. An untested `if` still fails the check.

## .gitignore for new projects

```
build/
*.o
*.gcda
*.gcno
```
