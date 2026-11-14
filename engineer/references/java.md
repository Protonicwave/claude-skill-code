# Java

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none. They use Maven.

## Detect

`pom.xml` and `.mvn/` for Maven, `build.gradle` or `build.gradle.kts` for Gradle.

## Tooling defaults for new projects

- Compiler with every lint warning on, warnings as errors, and Error Prone with NullAway as a plugin. In the `maven-compiler-plugin` configuration:

  ```xml
  <compilerArgs>
    <arg>-Xlint:all</arg>
    <arg>-Werror</arg>
    <arg>-XDcompilePolicy=simple</arg>
    <arg>--should-stop=ifError=FLOW</arg>
    <arg>-Xplugin:ErrorProne -Xep:NullAway:ERROR -XepOpt:NullAway:AnnotatedPackages=<base package></arg>
  </compilerArgs>
  <annotationProcessorPaths>
    <path><groupId>com.google.errorprone</groupId><artifactId>error_prone_core</artifactId><version>...</version></path>
    <path><groupId>com.uber.nullaway</groupId><artifactId>nullaway</artifactId><version>...</version></path>
  </annotationProcessorPaths>
  ```

  Error Prone needs JDK 21 or newer, and the `--add-exports` and `--add-opens` lines from its installation page in `.mvn/jvm.config`. Its findings are compile errors by default. NullAway treats every unannotated parameter, return value and field as non-null, so mark the ones that may be null with `@Nullable` (from `org.jspecify`). Take each version from the project's release page when adding it.

- PMD with `pmd:check` bound in the build and a project ruleset, `pmd-ruleset.xml`, named under `<rulesets>`:

  ```xml
  <rule ref="category/java/bestpractices.xml/UnusedPrivateField"/>
  <rule ref="category/java/bestpractices.xml/UnusedPrivateMethod"/>
  <rule ref="category/java/bestpractices.xml/UnusedLocalVariable"/>
  <rule ref="category/java/design.xml/CognitiveComplexity"/>
  <rule ref="category/java/design.xml/CyclomaticComplexity"/>
  ```

  `pmd:check` fails the build on any violation by default (`failOnViolation`, `failurePriority` 5). Set `printFailingErrors` so the log names each one. `CognitiveComplexity` reports from 15 and `CyclomaticComplexity` from 10 per method; they are review aids, as `standards.md` describes.

- SpotBugs with `spotbugs:check` bound in the build. It fails the build on a finding, including unused and unread fields, private methods never called, and strings concatenated with `+` in a loop.
- Before each commit, `mvn clean verify`. It compiles, tests, and runs PMD, SpotBugs and the coverage check.
- Dead code: PMD and SpotBugs find unused private members only. Search for callers of each public name the diff adds, as `standards.md` says.
- Dependency audit: `osv-scanner scan -r .`, which reads `pom.xml`, resolves transitive dependencies, and exits 1 on a known vulnerability. It cannot be added to the pom, so where it is not installed, say in the report and the pull request that the audit did not run. The OWASP dependency-check Maven plugin can live in the pom, but version 13 stops without an NVD API key, a credential only the user can supply.
- Style: Google Java Style where the repository has none: two-space blocks, a 100-column limit.

## Types

- `Optional` is meant for return types where a missing result is likely to cause errors. A variable of type `Optional` is never itself `null`.
- Use a record for immutable data: it is a transparent carrier with `equals` and accessors generated.

## Errors and resources

- Open every `AutoCloseable` in a try-with-resources statement. It is closed whether the block completes normally or not, and an exception from closing is suppressed behind the one from the block.
- `HttpRequest` without `timeout(...)` blocks forever waiting for a response, and an unset `connectTimeout` on `HttpClient` has no limit either. Set both.
- Build SQL with `PreparedStatement`: `?` markers in the text, values through the typed setters, parameter indexes from 1.

## Performance

Traps that change the complexity class, from the JDK documentation:

- `ArrayList.remove(int)` shifts every later element, so removing from the front in a loop is quadratic. Use `ArrayDeque` for a queue.
- `LinkedList.get(int)` walks the list from the nearer end. Indexing it in a loop is quadratic: iterate, or use an `ArrayList`.
- `String` is immutable, so `+=` in a loop copies the string each time. Use a `StringBuilder`.
- A `HashMap` rehashes whenever its size passes capacity times load factor (0.75). When the number of entries is known, size it so that capacity is at least entries divided by 0.75.

## Tests

- JUnit, run by `mvn verify`.
- Coverage of critical modules with JaCoCo: `prepare-agent`, then `check` in `verify`, which fails the build by default. Limit the check to the critical classes with `<includes>` and require every line and branch:

  ```xml
  <rule>
    <element>CLASS</element>
    <limits>
      <limit><counter>LINE</counter><value>COVEREDRATIO</value><minimum>1.00</minimum></limit>
      <limit><counter>BRANCH</counter><value>COVEREDRATIO</value><minimum>1.00</minimum></limit>
    </limits>
  </rule>
  ```

  JaCoCo appends each run to `target/jacoco.exec`, so without `clean` the check counts lines that earlier runs covered and passes a test that was removed. Exception handlers are not branches, so test each one the module has.

## .gitignore for new projects

```
target/
```
