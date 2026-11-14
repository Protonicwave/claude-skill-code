# SQL

Follow the repository's existing tooling. The defaults below are for new projects or where the repository has none. Engine-specific rules are for PostgreSQL; check the manual of any other engine before applying them.

## Detect

`*.sql` files, a migrations directory, and `.sqlfluff` for lint settings.

## Tooling defaults for new projects

- SQLFluff, configured in `.sqlfluff` with the dialect set and every rule on:

  ```ini
  [sqlfluff]
  dialect = postgres
  ```

  `rules` defaults to `all` and `exclude_rules` to none, so leave both unset. Without a dialect SQLFluff stops with exit 2 and lints nothing. `sqlfluff dialects` lists the names.
- Before each commit, `sqlfluff lint <paths>`. It exits 1 on any violation, including an unused CTE (ST03), `SELECT *` (AM04), unqualified columns in a query over several tables (RF02) and inconsistent keyword case (CP01). Never pass `--nofail`, which forces exit 0.
- Dead code: ST03 finds an unused CTE. Nothing finds an unused table, column, view or function, so search the repository for references to each one the diff adds.

## Queries from application code

- Pass values as parameters, separate from the statement text, never by building the string. The placeholder depends on the driver: `$1` in the PostgreSQL protocol, and `?`, `:1`, `:name`, `%s` or `%(name)s` under Python's DB-API, as the driver's `paramstyle` declares. PostgreSQL's parameterised call also accepts only one statement per string, an extra defence against injection.
- When an identifier such as a table or column name comes from outside, it cannot be a parameter. Escape it with the driver's identifier quoting.

## Performance

- Read the plan with `EXPLAIN` before and after a query change. A sequential scan reads every row of the table; a filter that is not an index condition is checked against each row scanned. A plan on a toy-sized table does not predict one on a large table, so load the local database with data of realistic size first. `EXPLAIN ANALYZE` runs the statement, so use it only on a local database, as `git.md` says, and wrap a data-modifying statement in a transaction that rolls back. The rollback does not return sequence values the statement took.
- A multicolumn B-tree index works best with constraints on its leading columns: put the columns tested for equality first and the range column after them. Indexes of more than three columns rarely help; one column is usually enough.
- A query that filters on an expression, such as `lower(email)`, needs an index on that expression. The expression is computed on every insert and update, so add one only for a query that needs it.

## Migrations

- `CREATE INDEX` on a table in use blocks writes until it finishes. `CREATE INDEX CONCURRENTLY` does not, but it cannot run inside a transaction block, so it needs a migration that the tool does not wrap in one. If it fails it leaves an invalid index behind: drop it and run it again.
- `ALTER TABLE` takes an `ACCESS EXCLUSIVE` lock unless the manual says otherwise for that form. Adding a column with a volatile default, such as `clock_timestamp()`, rewrites the whole table and its indexes under that lock. A constant default is evaluated once, when the statement runs, and does not.
