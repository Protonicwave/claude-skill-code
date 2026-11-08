# Plan template

Save as `.plans/<task-slug>.md`. The plan is the single source of state for the task: a fresh chat must be able to continue from it and the repository alone, with nothing else. Write facts and decisions, not prose. Remove any section that would be empty except `Current state`.

```markdown
# <Task title>

Branch: <type>/<slug>
Base: <default branch>
Status: awaiting approval
Chat boundary: single chat | fresh chat per phase

## Goal

What is true when this is done, in observable terms. Two to four lines.

## Context

Facts from the repository that the plan relies on: stack and versions, relevant modules and their paths, conventions seen in recent commits.

Commands:
- install:
- test:
- lint:
- type-check:
- dead-code:
- build:

## Shape

The pieces, where the boundaries sit, how data flows. What is deliberately left untouched.

New pieces, each with the existing or planned code that calls it:

- <module, type, interface or config option>: called by <caller>.

Anything without a caller is cut before approval. This list is where over-building shows up while it is still cheap to remove.

## Performance

- Budget: <time, memory or query count> for <operation>, with <input size>.
- Measured by: <committed script or test>, run as <command>.
- Baseline: <figure before the change, if the code exists>.

## Critical modules

- <path>: <why a defect here is costly>.
- Checked by: <coverage command limited to these paths>.

## Decisions

- <Decision>. Why. Alternative rejected and why.

## Edges and failure modes

- <Case>: <behaviour>. Phase <n>.
- Not handled: <case>, because <reason>.

## Tests

- [ ] <behaviour> (phase <n>, first | alongside)

## Phases

### Phase 1: <outcome-named title>

Delivers: what works at the end of this phase.
Commits: planned commit subjects.

- [ ] Complete

## Current state

Phase 0 of <n>. Nothing implemented yet.

## Open questions

- <Question only the user can answer>
```

At the end of every phase, rewrite `Current state` to hold: the last commit hash and subject, what now works, what the next phase starts with, and anything learned that a fresh reader would otherwise rediscover the hard way. Keep it under ten lines.

When the user approves the plan, change `Status` to `in progress`. After the pull request is opened, change it to `complete`.
