---
name: engineer
description: Plan-first engineering workflow and strict code standards for production-quality code. Use this whenever the user asks to build, implement, add a feature, fix a bug, refactor, scaffold a project, or write any non-trivial code in a repository, even if they do not mention planning or standards, and whenever they say "continue" or "next phase" on planned work. Writes a local, never-committed plan in .plans/, executes it in tested phases with real commits, and enforces simple, bounded, verified code in UK English with no em dashes and no AI artefacts in the repository. Not for questions or explanations that change no code.
---

# Engineer

The goal is code a strong senior engineer would sign off: correct first, then simple, then fast to produce. Quality comes from verification that actually runs, not from adjectives. Speed comes from reading only what is needed, deciding once, and never redoing work.

## Reference files

Read these when the step below says to, not up front.

- `references/standards.md`: design, correctness, errors, naming, comments, tests, security, repository hygiene. Read before writing any code.
- `references/python.md` or `references/typescript.md`: read the one matching the repository's stack. For any other language, `standards.md` alone applies.
- `references/plan-template.md`: read when writing a plan.
- `references/git.md`: read before the first commit of the session and before writing a pull request.
- `scripts/check_diff.py`: mechanical checks for dashes, US spellings, emoji, plan and AI references. Run it as described below.

## Orient

Before any other action in a repository:

1. Read `README`, the tooling config (`pyproject.toml`, `package.json`, `tsconfig.json`, CI workflow files) and `git log --oneline -20`. Recent commits show the conventions actually in use, and those win over this skill on matters of local style.
2. Identify the commands for install, test, lint, type-check, dead-code check and build. If one cannot be found, say so and ask rather than guess.
3. Do not create `CLAUDE.md`, `AGENTS.md` or any other assistant file. The repository should contain only what the project needs.

If the directory is not a git repository and the task is a new project, run `git init -b main`.

## Choose the track

**Quick track**: the change is confined to one or two files, adds no new type, module or boundary, and the right fix is obvious. Skip the plan. Read `standards.md` and the language file, write the test first if it is a bug fix, make the change, run the checks, commit.

**Planned track**: everything else. When in doubt, plan: a plan costs a few hundred tokens, a wrong direction costs a rewrite.

If `.plans/` already holds a plan with unticked phases for the current branch, the request is a continuation. Go to Execute.

## Plan

1. Make sure the plan stays local. Find the exclude file with `git rev-parse --git-path info/exclude` and append `.plans/` if it is not already there. This keeps plans out of git without adding a line to `.gitignore`, so the repository shows no trace of them.
2. Read only the code the task touches. Use search to locate it before opening whole files.
3. Settle ambiguities. Anything recoverable from the repository or a sensible default, decide and record in the plan. Ask only about decisions that are genuinely the user's.
4. If the request is wrong, under-specified, or will not survive its obvious next variation, say so now and propose the alternative.
5. Write `.plans/<task-slug>.md` from `references/plan-template.md`. Keep it under about 150 lines: it is a working document, not an essay.
6. Stop. Give the user a five-line summary (goal, shape, phase list, chat boundary, anything you need from them) and the plan path. Wait for approval. Fixing direction here is cheap; after code exists it is not.

### Sizing phases

Each phase is a vertical slice that ends with something working, the full suite green, and at least one commit. Do not split by layer (scaffold, then logic, then tests): a layer cannot be tested alone, so defects hide until the end.

Use as few phases as the work allows. One is fine. Two to five is typical. More than six means the task should be split into separate plans. A phase should produce a diff a reviewer can read in one sitting.

### Chat boundary

Set it in the plan:

- **Single chat**: three or fewer phases of modest size. The context stays small enough that carrying it costs less than reloading.
- **Fresh chat per phase**: anything larger. A new chat starts from the plan file and the repository, which is the smallest accurate state there is. A long chat carries stale exploration, and automatic compaction drops detail unpredictably.

## Execute

1. Find the plan: the one in `.plans/` whose `Branch` matches the current branch and has unticked phases. If none or several match, ask.
2. Read the plan's `Current state`, then `git status` and `git log --oneline <base>..HEAD`. If the repository does not match what the plan says, stop and report the difference rather than build on a wrong assumption.
3. Read `standards.md`, the language file, and `git.md` if this is the first commit of the session.
4. Make sure you are on the plan's branch, creating it from the base if needed.
5. Do the next unticked phase:
   - Write tests as the plan's test list specifies: first for bug fixes and for logic with clear inputs and outputs, alongside for wiring and UI.
   - Implement.
   - While iterating, run the narrowest relevant tests. Before each commit, run the full suite, the linter, the type-checker and the dead-code check.
   - Review your own diff against the checklist below.
   - Stage, run `python <skill-dir>/scripts/check_diff.py`, fix anything it reports, then commit following `git.md`.
6. Update the plan: tick the phase and its tests, rewrite `Current state` (last commit, what works, what is next), and record any decision or deviation with its reason.
7. Continue:
   - **Single chat**: go straight to the next phase without asking.
   - **Fresh chat per phase**: stop and tell the user to start a new chat and run `/engineer` to continue.

Stop mid-phase and ask only if the plan turns out to be wrong, a check fails for a reason outside the phase's scope, a decision appears that is not recoverable from the repository, or the work is growing beyond the plan. Do not quietly expand scope.

## Finish

After the last phase:

1. Run every check on the whole branch and show what each produced.
2. Review the full branch diff (`git diff <base>...HEAD`) once more against the checklist, as a whole: duplication across phases only shows up here.
3. Run `python <skill-dir>/scripts/check_diff.py <base>..HEAD`, which also checks commit messages.
4. Write the pull request description following `git.md`, save it to a scratch file outside the repository, and run `check_diff.py --file <path>` on it.
5. If the repository has a GitHub remote, push the branch and open the pull request with `gh pr create`. Never merge. Without a remote, give the user the description.
6. Set the plan's `Status` to `complete`.
7. Report: what was run and what it produced, what is done and what is not, and the weakest point in the result with the condition under which it breaks.

## Self-review checklist

Run through this on every diff before committing. Each item is a common way generated code goes wrong.

- Anything with no current caller: function, file, parameter, config option, interface, layer.
- An abstraction with one implementation, unless it is a type that removes an illegal state.
- A `try`/`catch` that catches more than it can name, or that swallows, or logs and rethrows.
- An ignored return value, error or promise.
- A loop, collection, retry, queue or network call without an explicit bound or timeout.
- Validation repeated downstream of the boundary that already did it.
- A comment that restates the code, or mentions the plan, phases, the task or an assistant.
- A name that is vague (`data`, `info`, `handle`, `manager`, `util`, `helper`) or in US spelling.
- Formatting, renames or upgrades unrelated to the task.
- An edge case from `standards.md` that is neither handled nor listed as unhandled.

## Speed

- Search before reading. Read the part of a file you need, not the whole file.
- Make independent tool calls in parallel.
- Do not re-read a file you just wrote.
- Do not spawn subagents unless a search genuinely spans many directories.
- Decide and move on. Do not narrate options you will not take.

## Writing

All output, including code, comments, commits, pull requests and messages to the user, uses UK English and contains no em dashes. Identifiers that mirror an external interface keep that interface's spelling (`color` in CSS, `initialize` in a library API). No emoji, decorative banners or "Step 1:" narration in code or commits.
