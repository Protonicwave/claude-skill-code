# Rust

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`Cargo.toml` and `Cargo.lock`. Lint levels live in the `[lints]` tables of `Cargo.toml` (Cargo 1.74 or later), and lint thresholds in `clippy.toml`.

## Tooling defaults for new projects

- Lint levels in `Cargo.toml`, so every command sees the same set:

  ```toml
  [lints.rust]
  unsafe_code = "forbid"

  [lints.clippy]
  pedantic = { level = "warn", priority = -1 }
  cognitive_complexity = "warn"
  unwrap_used = "warn"
  ```

  A group sits at a lower priority than single lints, so a single lint can override it. `forbid` cannot be overridden further down. Pedantic is aggressive and has false positives: allow a lint where it is wrong, with a comment giving the reason.

- Restriction lints such as `unwrap_used` are chosen one at a time, never enabled as a group.
- Thresholds in `clippy.toml`:

  ```toml
  cognitive-complexity-threshold = 15
  allow-unwrap-in-tests = true
  ```

  `cognitive_complexity` is off unless enabled, and its threshold defaults to 25. The argument and line limits default to 7 and 100. These are review aids, as `standards.md` describes. In tests, a panic is a failure, which is what a test should do, so `unwrap` is allowed there.
- Before each commit, `cargo clippy --all-targets -- -D warnings`. It fails on any warning, the compiler's included.
- Dead code: the compiler's `dead_code` lint reports only unused items that are not exported. A `pub` item in a library that nothing calls passes it, so search for callers of each `pub` name the diff adds, as `standards.md` says.
- Unused dependencies: `cargo machete`, which exits 1 when it finds one. It is fast but imprecise, so confirm each finding before removing the dependency.
- Dependency audit: `cargo audit`, against the RustSec advisory database. It exits non-zero on a vulnerable crate. Commit `Cargo.lock`: without it, `cargo audit` generates one with `cargo update`, and audits versions no build has used. Where the repository has a `deny.toml`, run `cargo deny check` instead. It checks advisories, licences, bans and sources, and its exit code is a bitset of the checks that failed. Its licence and ban policies are the project's to set, so do not create a `deny.toml` unasked.

## Types

- Public error types are meaningful and well behaved (C-GOOD-ERR in the Rust API Guidelines).
- Types are `Send` and `Sync` where possible (C-SEND-SYNC).
- Casing follows RFC 430 (C-CASE).

## Errors

- Propagate with `?` from any function that returns `Result`: an `Err` returns early from the enclosing function.
- `unwrap` and `expect` panic on `Err`. Match on the error, use `unwrap_or`, `unwrap_or_else` or `unwrap_or_default`, or propagate it.
- An unused `Result` is a compiler warning, which `-D warnings` turns into a failure.

## Resources and I/O

- `std::sync::mpsc::channel` never blocks the sender, so a producer faster than its consumer grows memory without limit. Use `sync_channel(n)`: its buffer is fixed, and a send blocks while it is full.

## Performance

Traps that change the complexity class, each from the standard library documentation:

- `Vec::remove` and `Vec::insert` shift every later element, O(n). Use `swap_remove` when order does not matter, and `VecDeque` with `push_back` and `pop_front` for a queue.
- `Vec` and `HashMap` are the defaults. `BTreeMap` costs O(log n) per lookup against `HashMap`'s expected O(1): use it when keys must stay sorted.
- When the final size is known, `Vec::with_capacity` and `String::with_capacity` avoid reallocating as the collection grows.

## Tests

- `cargo test`.
- Coverage of critical modules with `cargo llvm-cov`. Branch coverage needs a nightly toolchain, so on stable the fallback in `standards.md` applies: full line coverage plus a test for each outcome of every condition. Also require full region coverage. A region is a span within a line, so it catches a branch that shares a line with code that ran, which line coverage counts as covered:

  ```sh
  cargo llvm-cov --fail-under-lines 100 --fail-under-regions 100 --ignore-filename-regex '<files outside the critical modules>'
  ```

  Both floors apply to the total, so the regex must exclude every file that is not critical. cargo llvm-cov has no include filter, and a lookahead such as `(?!...)` silently matches nothing, so the regex lists the other files. A file added later counts towards the total and fails the gate until the regex names it or the tests cover it.

## .gitignore for new projects

```
/target
```
