# C#

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none.

## Detect

`*.csproj`, `*.sln` or `*.slnx`, and `Directory.Build.props`. Analyser severities live in `.editorconfig`.

## Tooling defaults for new projects

- Build settings in `Directory.Build.props`, so every project in the solution gets them:

  ```xml
  <Project>
    <PropertyGroup>
      <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
      <AnalysisMode>All</AnalysisMode>
      <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
      <Nullable>enable</Nullable>
    </PropertyGroup>
    <ItemGroup>
      <AdditionalFiles Include="$(MSBuildThisFileDirectory)CodeMetricsConfig.txt" />
    </ItemGroup>
  </Project>
  ```

  The default analysis mode enables few rules. `All` enables every rule as a build warning except the code metrics rules and a short list of others, and `TreatWarningsAsErrors` turns each warning, NuGet's included, into an error. That brings in CA1031 (catching a general exception), CA2000 (a local disposable never disposed, though it misses some types), CA2200 (`throw e`, which loses the stack trace) and CA1851 (enumerating an `IEnumerable` twice). Nullable warnings fail the build too.

- `.editorconfig` for the rules `All` leaves out:

  ```ini
  root = true

  [*.cs]
  dotnet_diagnostic.CA1502.severity = warning
  dotnet_diagnostic.IDE0051.severity = warning
  dotnet_diagnostic.IDE0052.severity = warning
  ```

  CA1502 is cyclomatic complexity. Its threshold, 25 by default, is set in `CodeMetricsConfig.txt` with a line such as `CA1502: 10`; it is a review aid, as `standards.md` describes. IDE0051 (unused private member) and IDE0052 (private member written but never read) do not fail the build under `All` unless their severity is set here.
- Before each commit, `dotnet build`. It fails on any analyser, compiler, nullable or NuGet warning.
- Dead code: IDE0051, IDE0052 and CA1823 cover private members, and CA1812 internal classes never created. Nothing reports an unused public member, so search for callers of each public name the diff adds, as `standards.md` says.
- Dependency audit: NuGet audits on every restore, and from `net10.0` it includes transitive packages (`NuGetAuditMode` `all`). With `TreatWarningsAsErrors`, a vulnerable package fails `dotnet build` with NU1901 to NU1904, one code per severity. `dotnet list package --vulnerable` exits 0 even when it lists a vulnerable package, so it is a report, never the gate.

## Types

- `Nullable` enabled: `string` and `string?` are the same runtime type, so the annotations protect only as far as the warnings are errors.

## Errors

- When code cannot recover from an exception, do not catch it. CA1031 fails a `catch (Exception)`: catch a more specific type, or rethrow as the last statement of the handler. A process-boundary handler that must catch everything suppresses CA1031 there with the reason.
- Rethrow with `throw;`. `throw e` restarts the stack trace at the current method.
- Catch `OperationCanceledException`, not `TaskCanceledException`.

## Resources and I/O

- Dispose every `IDisposable`. A `using` declaration disposes at the end of the enclosing scope; a `using` statement disposes at the end of its block, so use it when release must come sooner. Both dispose when an exception is thrown.
- A disposable class that is not `sealed` calls `GC.SuppressFinalize(this)` in `Dispose` (CA1816). Seal it if it is not meant to be inherited.
- `HttpClient.Timeout` is 100 seconds by default. Set one that fits the call, and pass a `CancellationToken` for a per-request limit: the shorter of the two applies.
- Use `async` and `await` for I/O. Return `async Task`, not `async void`: an exception from `async void` cannot be caught by the caller. Do not block on a task with `.Result` or `.Wait()`.
- Build SQL with `@name` parameters on the command's `Parameters`, never by interpolating values into the text. A parameter is treated as a literal value, not as executable code.

## Idiom

- Follow the Microsoft C# coding conventions where the repository has no style. Use `var` only when the reader can infer the type from the expression.

## Performance

- A string modified an unknown number of times, as in a loop, belongs in a `StringBuilder`. A few fixed changes do not need one.
- An `IEnumerable` is not cached: each enumeration reruns the query behind it, which may be a database call. Materialise it once with `ToList()` or `ToArray()` when it is read more than once. CA1851 flags the repeat.

## Tests

- `dotnet test`.
- Coverage of critical modules with coverlet. Add the `coverlet.msbuild` package to the test project, then:

  ```sh
  dotnet test -p:CollectCoverage=true -p:Threshold=100 -p:ThresholdType=line%2cbranch -p:Include="[<Assembly>]<Namespace.Class>"
  ```

  It fails the run when line or branch coverage of an included module falls below the threshold. `%2c` is an escaped comma, which MSBuild needs in a property value. `Include` limits the check to the critical classes; without it every instrumented module must reach the threshold.

## .gitignore for new projects

Generate it with `dotnet new gitignore`. It ignores `[Bb]in/`, `[Oo]bj/`, `.vs/` and `*.user`, among others.
