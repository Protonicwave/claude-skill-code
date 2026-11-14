# Code standards

These apply to every language. The language file adds tooling and idiom on top. Where the repository already does something a particular way, follow the repository unless doing so would break correctness.

Several rules here come from NASA JPL's "Power of 10" and TigerBeetle's "TigerStyle", adapted for application code. The common idea: make the code simple enough to reason about, put explicit limits on everything, and fail loudly at the first sign of a wrong state.

## Design

- Build the simplest design that meets the current requirement. Design for the next requirement only when it is known, not imagined.
- No abstraction, interface, base class or configuration option without a current second caller or implementation. The exception: a wrapper type that makes an illegal state unrepresentable is justified at one caller.
- Module boundaries follow the domain, not the framework's folder layout. A change to one business rule should touch one place.
- Dependencies point inward: domain logic does not import I/O, frameworks or transport. Nothing reaches into another module's internals.
- Separate decisions from effects. A function that decides should not also read files, call the network or write to a database. This makes the decision testable without fakes.
- State lives in one place. Derived values are computed, not stored and synchronised. A cache is a named exception with a stated invalidation rule.
- Composition over inheritance. Explicit wiring over decorators, reflection or convention-based discovery.
- Prefer the design that is easiest to delete.
- DRY applies to knowledge, not to text. Two pieces of code that look alike but change for different reasons stay separate.

## Correctness

- **Bound everything.** Every loop over external input, every retry, queue, buffer, recursion, batch, upload and network call has an explicit limit or timeout. The limit is a named constant with a unit in its name (`MAX_RETRIES`, `REQUEST_TIMEOUT_SECONDS`), and the behaviour at the limit is defined.
- **No recursion over input whose depth you do not control.** Use iteration with an explicit stack.
- **Check every result.** No ignored return value, error, status code or promise. If a result is deliberately ignored, the code says so explicitly and a comment says why.
- **Make illegal states unrepresentable.** Use the type system: enums or literal unions for closed sets, distinct types for identifiers, discriminated unions for states, non-optional fields where a value is always present.
- **Validate once, at the boundary.** Anything from outside the process (HTTP, files, environment, CLI arguments, rows other systems write) is parsed into a trusted type at entry. Inward code trusts the type and does not re-check.
- **Assert invariants.** Where a condition can only be false because of a bug, assert it, so the bug surfaces where it happens rather than three calls later. Assertions are for programmer errors, never for validating input or for control flow.
- **Short functions, one level of abstraction.** A function should fit on one screen, roughly 60 lines. Nesting deeper than three levels is a sign to extract or return early. These limits, and the linter's complexity limits, are review aids: they mark code a reader cannot follow in one pass. The evidence that they prevent defects is weak, so restructure for the reader's sake, and suppress a single finding, with the reason, only where splitting would be harder to read, such as a flat lookup table.
- **Smallest scope.** Declare variables where they are used. No mutable module-level state.
- **Strictest checks the repository tolerates.** Type-checker and linter at their strictest practical settings, warnings treated as errors. No suppression without a comment stating why the checker is wrong in that instance.

## Edges

For every input, decide the behaviour for: empty, single item, duplicates, out of order, oversized, malformed, missing dependency (file, service, environment variable), and concurrent access where relevant. Handle each or state that it is not handled and why. A handled edge has a test.

## Errors and logging

- Handle the failures you can name. Let everything else propagate.
- No catch-all handlers except at the process boundary (request handler, CLI entry point, worker loop), where the error is logged once with context and turned into the right response or exit code.
- Fail at the point of the mistake. Error messages name the offending value and what was expected: `expected positive quantity, got -3`, not `invalid input`.
- Preserve the cause when wrapping an error.
- Never swallow an error. Never log and rethrow: the error gets logged twice and the context is duplicated.
- Log at boundaries and on state changes that matter operationally, with structured fields rather than interpolated prose. Never log secrets, tokens or personal data.

## Performance

Choose the right complexity up front: no query per row in a loop, no loading unbounded data into memory, stream or paginate anything whose size you do not control, use the right data structure for lookups. Beyond that, measure before optimising. Clear code at the right complexity class beats clever code.

When the task states a time, memory or query budget, or exists to make something faster, the budget is a requirement like any other; for a speed-up with no stated figure, set one in the plan and tell the user. A task with neither gets no budget and no timing script: a refactor or bug fix keeps the complexity it had.

- Write it down with the input size it applies to: "one lookup under 20 µs with the full ranges file loaded", not "fast". For a speed-up, measure the existing code first and report both figures.
- Commit a script or test that measures it on that input and prints the figure next to the budget, and give its command in the README, so a later change can find and rerun it. Start a fresh process, time many repetitions inside it, and report the median. A timing assertion in the default suite fails on a slow CI runner, so keep it out unless its threshold is several times the budget.
- Run it before each commit that touches the measured code, and report the measured figure, not "within budget".

## Naming

- Precise and descriptive. A name says what the thing is or does in the domain's vocabulary.
- No `Manager`, `Helper`, `Handler`, `Util`, `Data`, `Info` unless the thing genuinely is one.
- Booleans read as predicates (`is_expired`, `has_access`). Quantities carry units (`timeout_ms`, `size_bytes`).
- UK English (`normalise`, `colour`, `behaviour`, `initialise`), except where mirroring an external interface.

## Comments and documentation

- Comments explain why: a constraint, a trade-off, a non-obvious consequence, a link to a specification. Never what the next line does.
- No comment mentions the plan, a phase, the task, a conversation, or an assistant. No "new", "updated", "improved" or "now": comments describe the code as it is, not its history.
- Docstrings on public API only, short, stating contract and failure modes rather than restating the signature.
- No apologetic, promotional or filler language ("robust", "seamless", "comprehensive", "simply", "note that").
- `README.md` covers what the project is, how to install, run and test it, and how to configure it. Nothing else.

## Tests

- Bug fixes start with a test that reproduces the bug and fails.
- Logic with clear inputs and outputs (calculations, parsing, validation, business rules): test first.
- Wiring, scaffolding, UI: tests alongside the code.
- Test observable behaviour through the module's public interface. No tests of private functions.
- Real objects by default. Fakes only at I/O boundaries: network, clock, filesystem, external processes. A fake at a boundary may assert what was sent to it; nothing else asserts call counts.
- One behaviour per test, named for the behaviour (`rejects_negative_quantity`).
- Every handled edge case has a test.
- A plan lists its critical modules, if it has any: those the task's correctness rests on, or where a defect loses money, data or access. Each has full line and branch coverage from the suite, checked before every commit that touches it. A line that needs no test, such as an entry point that only wires tested parts together, is excluded with the coverage tool's pragma and the reason on the same line. Coverage proves the code ran, not that the assertions are right: it finds untested code, it does not certify tested code.
- The full suite passes before every commit. A test is never deleted, skipped or weakened to make the suite pass. A failure unrelated to the change is reported, not fixed in passing.

## Gates

A gate is a check that blocks a commit: the suite, linter, type-checker, dead-code check, coverage check, dependency audit or a performance measurement.

- **Every gate can fail.** It exits non-zero on a finding. Nothing in its configuration reduces findings to output: no report-only mode, no threshold nothing can fall below, no option that passes when the tool cannot reach its service. When you add a gate or change its configuration, plant one finding it should catch, run it, see it fail, then remove the finding. A gate that has never failed is unproven.
- **Dead code is looked for across the whole program.** A compiler warning for unused private members misses a public function nothing calls. Use the whole-program tool the language file names. Where it names none, search the repository for callers of each public name the diff adds.
- **Coverage falls back where branches cannot be measured.** Where the toolchain reports only line or statement coverage, a critical module needs full line coverage plus a test for each outcome of every condition in it, listed in the plan's test list.

## Security

- Untrusted input is validated at the boundary (see Correctness).
- Queries and shell commands are parameterised, never built from strings.
- Least privilege for anything created: tokens, roles, file permissions, container users.
- Secrets never appear in code, logs, error messages or test fixtures.
- A change touching authentication, cryptography, permissions or sessions states the threat it defends against before it is written.
- The linter's security rules are on, as the language file names them. Review alone does not catch insecure generated code: in one study about 40% of 1,689 generated programs were vulnerable.
- The dependency audit is a gate. Run the language file's audit command before every commit that changes a manifest or lock file, and before opening a pull request. Fix a finding by upgrading. When no fixed version exists, or the vulnerable code is unreachable from this project, ignore that one advisory by its identifier in the tool's configuration with the reason beside it, and say so in the pull request. Never lower the severity level or skip the audit to get past a finding.

## Dependencies

Prefer the standard library. A new dependency must replace more than about fifty lines of code you would otherwise understand and own. It is pinned, checked for maintenance status and known vulnerabilities, and justified in one line in the commit body.

## Repository hygiene

- Every file exists because the project needs it. No placeholder modules, empty directories or speculative configuration.
- `.gitignore` is the standard one for the stack (see the language file), not a catalogue of every tool in existence.
- No assistant artefacts: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.claude/`, prompt logs, scratch notes, plan files.
- No Markdown files other than `README.md` unless the repository already has them. Existing ones are left alone.
- Change only what the task requires. No drive-by renames, reformatting or dependency upgrades.
