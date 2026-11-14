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
2. Identify the commands for install, test, lint, type-check, dead-code check, dependency audit and build. If one cannot be found, say so and ask rather than guess.
3. Do not create `CLAUDE.md`, `AGENTS.md` or any other assistant file. The repository should contain only what the project needs.
4. Prepare the repository, once. Both steps are local to this clone and never committed, so the repository shows no trace of them.
   - Find the exclude file with `git rev-parse --git-path info/exclude` and append `.plans/` if it is not already there. Plans then stay out of git without a `.gitignore` line.
   - Install the style check as `pre-commit` and `commit-msg` hooks, so no change or commit message can skip it. Find the hooks directory with `git rev-parse --git-path hooks`. If `git config core.hooksPath` is set, leave both alone: the repository manages its own hooks, and you run the checks by hand instead. Otherwise write each hook that does not already exist, or that exists with the marker line below, and make it executable. Leave a hook without the marker alone and run its check by hand.

     ```sh
     #!/bin/sh
     # engineer-style-check
     exec <python> "<absolute skill-dir>/scripts/check_diff.py"
     ```

     ```sh
     #!/bin/sh
     # engineer-style-check
     exec <python> "<absolute skill-dir>/scripts/check_diff.py" --commit-msg "$1"
     ```

     `<python>` is whichever of `python3` or `python` runs Python 3.12 or later in this shell. Skip the hooks in the repository that holds this skill: its files have to mention plans and attribution.

If the directory is not a git repository and the task is a new project, run `git init -b main` first.

## Choose the track

**Quick track**: the change is confined to one or two files, adds no new type, module or boundary, and the right fix is obvious. Skip the plan. Read `standards.md` and the language file, write the test first if it is a bug fix, make the change, run the checks, commit.

**Planned track**: everything else. When in doubt, plan: a plan costs a few hundred tokens, a wrong direction costs a rewrite.

If `.plans/` already holds a plan with unticked phases for the current branch, the request is a continuation. Go to Execute.

## Plan

1. Read only the code the task touches. Use search to locate it before opening whole files.
2. Settle ambiguities. Anything recoverable from the repository or a sensible default, decide and record in the plan. Ask only about decisions that are genuinely the user's.
3. If the request is wrong, under-specified, or will not survive its obvious next variation, say so now and propose the alternative.
4. Write `.plans/<task-slug>.md` from `references/plan-template.md`. Keep it under about 150 lines: it is a working document, not an essay.
5. Stop. Give the user a five-line summary (goal, shape, phase list, chat boundary, anything you need from them) and the plan path. Wait for approval. Fixing direction here is cheap; after code exists it is not.

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
   - While iterating, run the narrowest relevant tests. Before each commit, run the full suite, the linter, the type-checker and the dead-code check, plus the dependency audit if the commit changes a manifest or lock file, the plan's coverage check if the commit touches a critical module and its performance measurement if it touches the measured code. A critical module below full coverage, or a measurement over budget, means the phase is not done.
   - Review your own diff against the checklist below.
   - Stage and commit following `git.md`. The hooks run the style check on the staged diff and on the message, and block the commit on any error: fix the cause and commit again. Where a hook could not be installed, run its check yourself: `check_diff.py` before committing, and `check_diff.py --commit-msg <file>` on the message, written to a scratch file first.
6. Update the plan: tick the phase and its tests, rewrite `Current state` (last commit, what works, what is next), and record any decision or deviation with its reason.
7. Continue:
   - **Single chat**: go straight to the next phase without asking.
   - **Fresh chat per phase**: stop and tell the user to start a new chat and run `/engineer` to continue.

Stop mid-phase and ask only if the plan turns out to be wrong, a check fails for a reason outside the phase's scope, a decision appears that is not recoverable from the repository, or the work is growing beyond the plan. Do not quietly expand scope.

## Finish

After the last phase:

1. Run every check on the whole branch and show what each produced.
2. Get an independent review. Spawn one fresh subagent, router-expert if the model-router skill is installed, and give it only: the base branch name, the path to `references/standards.md`, and the self-review checklist below. Do not give it the plan or your reasoning: a reviewer who knows why each piece exists will accept it, which is exactly the blind spot being covered. Ask it to read `git diff <base>...HEAD` and report, with file and line, anything over-built (a piece that could be deleted or inlined without losing a requirement), anything it had to read twice to follow (a name, branch or function whose purpose was not clear on first reading), any defect, and any unhandled edge.

   Settle every finding with evidence, not opinion, because the author is the person least able to judge their own code:

   - **Over-built**: delete or inline the piece and run the suite. Green with no requirement lost: the piece goes. Green but a requirement is lost: the piece stays, and the missing test that should have caught its removal is the real defect, so add it. Either way the finding produces a change.
   - **Hard to read**: rewrite the passage the reviewer named, by renaming, extracting a function or returning early, and run the suite. Green: keep the rewrite. Red: the rewrite changed behaviour, so undo it and try a smaller one. A comment or a reply explaining the code does not settle it: if it needed explaining, it needed rewriting.
   - **Defect or unhandled edge**: write the test that would expose it. If it fails, fix the code. If it passes, the finding is disproved and the test stays in the suite as proof.
   - **Neither settles it**: send your reasoning back to the same reviewer once. If the reviewer still holds the finding, stop and put it to the user before opening the pull request. Nothing is rejected silently.

   Commit each fix separately. On the quick track, amend the fixes into the change's commit instead, so a small fix lands as one commit. Nothing is pushed before step 5, so the amend rewrites nothing shared.
3. Run `python <skill-dir>/scripts/check_diff.py <base>..HEAD`, which also checks commit messages.
4. Write the pull request description following `git.md`, save it to a scratch file outside the repository, and run `check_diff.py --file <path>` on it.
5. If the repository has a GitHub remote, push the branch and open the pull request with `gh pr create`. Never merge. Without a remote, give the user the description.
6. Set the plan's `Status` to `complete`.
7. Report: what was run and what it produced, including each measured figure against its budget, what the reviewer found and what was done about it, what is done and what is not, and the weakest point in the result with the condition under which it breaks.

## Self-review checklist

Run through this on every diff before committing. Each item is a common way generated code goes wrong.

- Anything with no current caller: function, file, parameter, config option, interface, layer.
- An abstraction with one implementation, unless it is a type that removes an illegal state.
- A `try`/`catch` that catches more than it can name, or that swallows, or logs and rethrows.
- An ignored return value, error or promise.
- A loop, collection, retry, queue or network call without an explicit bound or timeout.
- Validation repeated downstream of the boundary that already did it.
- Untrusted input reaching a query, shell command, file path or template without validation or parameters, or a secret in code, a log or a fixture.
- A comment that restates the code, or mentions the plan, phases, the task or an assistant.
- A name that is vague (`data`, `info`, `handle`, `manager`, `util`, `helper`) or in US spelling.
- Formatting, renames or upgrades unrelated to the task.
- An edge case from `standards.md` that is neither handled nor listed as unhandled.

## Speed

- Search before reading. Read the part of a file you need, not the whole file.
- Make independent tool calls in parallel.
- Do not re-read a file you just wrote.
- Do not spawn subagents except the reviewer in Finish, a search that genuinely spans many directories, or a step the model-router skill assigns to a tier when that skill is installed.
- Decide and move on. Do not narrate options you will not take.

## Writing

All output, including code, comments, commits, pull requests and messages to the user, uses UK English and contains no em dashes. Identifiers that mirror an external interface keep that interface's spelling (`color` in CSS, `initialize` in a library API). No emoji, decorative banners or "Step 1:" narration in code or commits.
