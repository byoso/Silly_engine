[silly_orm index](00_silly_orm_index.md)

# Backend agnostic

`Silly_ORM` is designed to run with different SQL backends through connectors.

Current state:

- SQLite: primary and fully tested backend.
- PostgreSQL: supported via `PostgresConnector`, with dedicated integration tests.

## Connector model

The ORM core (`SillyDb`, `Table`, `Query`, migration helpers) talks to a connector interface.
Each connector is responsible for:

- opening/closing the connection,
- executing SQL,
- mapping placeholders,
- commit/rollback behavior.

## SQLite usage

```python
from silly_engine.silly_orm.db import SillyDb

db = SillyDb("DB.sqlite3")
```

## PostgreSQL usage

```python
from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.connectors.postgres import PostgresConnector

dsn = "postgresql://silly:silly@localhost:5432/silly_engine_test"
db = SillyDb(connector=PostgresConnector(dsn))
```

### Postgres local for dev (reminder)

```bash
docker pull postgres:16.3

docker run --name silly-postgres \
	-e POSTGRES_USER=silly \
	-e POSTGRES_PASSWORD=silly \
	-e POSTGRES_DB=silly_engine_test \
	-p 5432:5432 postgres:16.3
```


## Notes on SQL differences

Some SQL operations are backend-specific. `Silly_ORM` handles these internally where needed.

Examples:

- Placeholder style (`?` vs `%s`) is handled by connectors.
- Schema introspection differs (`sqlite_master/PRAGMA` vs `information_schema/pg_indexes`).
- Conflict-safe MTM insert differs (`INSERT OR IGNORE` vs `ON CONFLICT DO NOTHING`).

## Migration guidance

For cross-backend migration scripts:

- prefer `safe_*` helpers from `migration_helpers`,
- avoid backend-specific raw SQL unless necessary,
- keep migrations idempotent and small.

## Running backend-specific tests

PostgreSQL tests are in `tests/tests_silly_orm_postgres/` and require:

- `psycopg2-binary` installed,
- `TEST_POSTGRES_DSN` environment variable set.

Example:

```bash
TEST_POSTGRES_DSN='postgresql://silly:silly@localhost:5432/silly_engine_test' \
python -m pytest tests/tests_silly_orm_postgres -v
```

## CI

CI runs both backends:

- SQLite-focused suite
- PostgreSQL integration suite (with a Postgres service container)

Workflow file:

- `.github/workflows/tests.yml`
