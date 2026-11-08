# TypeScript

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`package.json`, `tsconfig.json`. The lock file tells you the package manager: `package-lock.json` is npm, `pnpm-lock.yaml` is pnpm, `yarn.lock` is yarn, `bun.lock` or `bun.lockb` is bun. Use that one and never mix them.

## Tooling defaults for new projects

- ESM (`"type": "module"`), current LTS Node.
- `tsconfig.json`:

  ```json
  {
    "compilerOptions": {
      "strict": true,
      "noUncheckedIndexedAccess": true,
      "exactOptionalPropertyTypes": true,
      "noImplicitOverride": true,
      "noFallthroughCasesInSwitch": true,
      "verbatimModuleSyntax": true
    }
  }
  ```

- ESLint with `typescript-eslint`'s `strictTypeChecked` config, or Biome if the repository uses it. Make sure these are on: `no-floating-promises`, `no-misused-promises`, `no-explicit-any`, `switch-exhaustiveness-check`.
- Size and complexity limits as lint errors: `complexity: 10`, `max-depth: 3`, `max-params: 4`, `max-lines-per-function: 60`. A failure is a design signal: restructure rather than raise the limit.
- Knip, run in CI and before each commit, to catch unused files, exports and dependencies. It finds the code nothing calls, which is the commonest form of over-building.
- Vitest for tests, unless the repository uses another runner.

## Types

- No `any`. Use `unknown` at boundaries and narrow it with runtime validation: zod if the repository has it or the validation is substantial, hand-written type guards otherwise.
- Discriminated unions for states. Exhaustive `switch` ending in a `never` check.
- Branded types for identifiers that must not be mixed up.
- `readonly` properties and `ReadonlyArray` by default.
- `as` casts only immediately after validation. A non-null `!` only with a comment proving the value is present.

## Errors

- Throw `Error` subclasses, never strings or plain objects. Pass `{ cause }` when wrapping.
- `catch (error: unknown)` and narrow before use. No empty `catch` blocks.
- Every promise is awaited, returned, or explicitly handled. No fire-and-forget without a comment saying why it is safe.
- Use Result types only if the repository already uses them.

## Async and I/O

- Every `fetch` gets a timeout: `signal: AbortSignal.timeout(ms)`.
- `Promise.all` for independent work. Bounded concurrency when mapping over a list whose size you do not control.
- Check `response.ok` before reading the body.

## Performance

Traps that change the complexity class or stall a server:

- `array.includes` or `indexOf` inside a loop scans the array every time. Build a `Set` once: `has` is sublinear on average by specification.
- `array.shift()` moves every remaining element. For a queue, keep a head index into the array instead.
- `await` inside a loop over independent operations runs them one after another. Start them together and `Promise.all` the results, except where each operation holds a bounded resource (memory, file descriptors, connections) or order matters: there, keep the loop or bound the concurrency.
- In Node.js, every request callback shares one event loop, so work that grows with client input delays every other client. Reason about each handler's complexity in terms of the input the client controls.
- The synchronous APIs (`readFileSync`, `execSync`, `zlib` and `crypto` `*Sync` calls) are for scripts, never a request path.
- `JSON.parse` and `JSON.stringify` are linear but slow on large input. Cap the size of a client's body before parsing it.

## Idiom

- Named exports. Default exports only where a framework requires them.
- No barrel `index.ts` files in application code: they create import cycles and slow builds.
- `const` by default. No `var`. No classes where a function and a type will do.
- `Map` and `Set` for keyed lookups rather than object literals.
- Constants in `UPPER_SNAKE_CASE` with units in the name.

## Tests

- Test files next to the code (`thing.test.ts`) or in `tests/`, matching the repository.
- `it.each` for edge-case tables.
- Fake timers and the network only at the boundary. Do not mock internal modules.
- Commands: the scripts in `package.json`. For new projects, define `test`, `lint`, `typecheck` (`tsc --noEmit`) and `build`.
- Coverage of critical modules with Vitest and `@vitest/coverage-v8`: `vitest run --coverage --coverage.include=<paths> --coverage.thresholds.100`. Exclude code with `/* v8 ignore next */` and a comment giving the reason.

## .gitignore for new projects

```
node_modules/
dist/
build/
coverage/
*.log
.env
.env.*
!.env.example
```

Add framework output directories (`.next/`, `.svelte-kit/`, `.turbo/`) only when that framework is in use.
