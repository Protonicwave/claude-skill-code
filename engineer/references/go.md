# Go

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`go.mod` and `go.sum`. Lint configuration in `.golangci.yml`, which starts with `version: "2"`, the only value golangci-lint 2 accepts.

## Tooling defaults for new projects

- `go vet ./...`. It exits non-zero when it reports a problem.
- golangci-lint 2 as the linter, configured in `.golangci.yml`:

  ```yaml
  version: "2"
  linters:
    default: standard
    enable:
      - gocognit
      - gocyclo
      - gosec
      - unparam
    settings:
      gocognit:
        min-complexity: 15
      gocyclo:
        min-complexity: 10
  ```

  Run `golangci-lint run ./...`. The `standard` set includes `errcheck`, which fails on an unchecked error, and `unused`. `gosec` is the security scanner. `gocognit` and `gocyclo` default to 30, and their documentation recommends 10 to 20; they are review aids, as `standards.md` describes.

- Dead code: `unused` reports unexported identifiers only. An exported function nothing calls passes it, so search for callers of each exported name the diff adds, as `standards.md` says.
- Unused requirements: `go mod tidy -diff` changes nothing and exits non-zero when `go.mod` or `go.sum` is not tidy.
- Dependency audit: `govulncheck ./...`. It exits non-zero when the code calls a function with a known vulnerability. A vulnerable module whose affected code is never called is listed without failing the run. A structured output format, such as `-format json`, exits 0 whatever it finds, so never use one as the gate. govulncheck cannot silence a finding: upgrade the module, or say in the pull request why the finding stands.

## Types

- Do not pass pointers as arguments only to save a few bytes.
- A `context.Context` is a parameter of each method that needs it, never a field of a struct.

## Errors

- Never discard an error with `_`. If a function returns an error, check it.
- Handle the error first and return, so the normal path stays at the lowest indentation.

## Resources and I/O

- `defer` the release of a resource straight after acquiring it, so it runs on every return path.
- Say when, or whether, each goroutine you start exits. A goroutine blocked forever on a channel send or receive is a leak.
- Bound fan-out over input you do not control. `errgroup.Group.SetLimit(n)` from `golang.org/x/sync` caps the active goroutines at `n`, and `Go` blocks until one finishes.

## Idiom

- Share memory by communicating over channels, but not everywhere: a counter shared between goroutines may be best guarded by a mutex.

## Performance

- Build strings with `strings.Builder`, which keeps memory copying to a minimum, and call `Grow(n)` first when the size is known.
- When a slice's final length is known, create it with `make([]T, 0, n)`. Otherwise `append` reallocates and copies whenever the capacity runs out.
- Before Go 1.23, a `time.After` timer was not collected until it fired, so on older Go a loop that creates one per iteration holds every timer until it fires.

## Tests

- `go test -race ./...`. The race detector costs 5x to 10x in memory and 2x to 20x in time, so keep benchmarks out of race runs.
- Go measures statement coverage, not branch coverage, so the fallback in `standards.md` applies to a critical module: full coverage of its statements plus a test for each outcome of every condition. Check it by file, which fails when any function in the file is below 100% and when the file is missing from the profile:

  ```sh
  go test -coverpkg=./... -coverprofile=cover.out ./...
  go tool cover -func=cover.out | awk -v f='/<module>.go:' 'index($1, f) { n++; if ($NF != "100.0%") bad++ } END { exit (n == 0 || bad > 0) }'
  ```

  `-coverpkg=./...` measures every package from every test, rather than only the package each test belongs to.

## .gitignore for new projects

```
cover.out
```
