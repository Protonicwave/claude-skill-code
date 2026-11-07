# Git

## Branches

- Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`. Without a remote, use whichever of `main` or `master` exists.
- Work on a branch named `<type>/<slug>`, for example `feat/order-export` or `fix/negative-quantity`. Never commit to the default branch.
- In a brand-new repository, the scaffold commit (`.gitignore`, `README.md`, tooling config) goes on `main` so there is a base to branch from. Everything after it goes on a branch.

## Commits

Commit when each logical change is complete and the full suite passes. One logical change per commit: a phase may be one commit or several, never a mix of unrelated changes.

Format: Conventional Commits.

```
<type>(<optional scope>): <subject>

<body>
```

- Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`.
- Subject: imperative mood, lower case after the prefix, no full stop, under 72 characters.
- Body: why the change was needed and what trade-off was taken. Wrapped at 72 characters. Omit it for trivial changes. A new dependency gets a one-line justification here.
- No trailers: no `Co-Authored-By`, no "Generated with", no tool attribution of any kind.
- No mention of the plan, phases, the task, a conversation or an assistant. The history should read as an engineer's account of the change.
- No `WIP`, "fix typo" or "address review" commits. Fix the change before committing it.

Examples:

```
fix(orders): reject negative quantities at the API boundary

Negative quantities reached the pricing engine and produced credits.
Validation now happens when the request is parsed, so pricing can
assume a positive quantity.
```

```
feat(export): stream order export as CSV

Exports above 50k rows exhausted worker memory. Rows are now written
as they are read, at the cost of no longer sorting by total.
```

## Pull requests

Title: the same format as a commit subject.

Body, in this order:

- **Context**: the problem and why it matters.
- **Changes**: what changed, described by behaviour, not as a per-file list.
- **Testing**: what was run and what it showed.
- **Risks**: what could break and under which conditions.
- **Rollback**: how to undo it safely.

Same rules as commits: UK English, no em dashes, no mention of plans, phases or assistants, no attribution.

Open it with `gh pr create --base <base> --title "<title>" --body-file <path>`. Never merge.

## Hard stops

Never do these without an explicit instruction from the user in the current session:

- Force push, or amend or rewrite anything already pushed.
- Delete branches or tags.
- Resolve a merge conflict by discarding one side.
- Run migrations against anything other than a local database.
- Touch secrets or credentials.
- Edit generated files by hand.
- Install tooling outside the repository.
- Commit assistant artefacts: plan files, `.claude/`, prompt logs, scratch notes.
