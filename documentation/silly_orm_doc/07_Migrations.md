[silly_orm index](00_silly_orm_index.md)

# Migrations

Use versioned function-based migrations with `db.migrate([...])`.

```python
def mig_1_0_0(db):
    db.execute("ALTER TABLE knights ADD COLUMN title TEXT")


def mig_1_1_0(db):
    db.execute("UPDATE knights SET title = ? WHERE title IS NULL", ("Sir",))


db.migrate([
    ("1.0.0", mig_1_0_0),
    ("1.1.0", mig_1_1_0),
])
```

## Notes

- Migration functions receive `db` as parameter.
- Apply migrations before declaring/using app tables at startup.
- On failure, migration errors are raised as `SillyDbError`.

## Migration helpers

Use prebuilt helpers from `migration_helpers` to keep migrations simple and idempotent.

```python
from silly_engine.silly_orm.migration_helpers import (
    introspect_table_exists,
    introspect_column_exists,
    introspect_index_exists,
    introspect_table_columns,
    introspect_table_indexes,
    schema_rename_table,
    schema_add_column,
    schema_rename_column,
    schema_drop_column,
    schema_create_index,
    schema_drop_index,
    safe_rename_table,
    safe_add_column,
    safe_rename_column,
    safe_drop_column,
    safe_create_index,
    safe_drop_index,
)
```

### Naming convention

- `introspect_*`: read schema metadata, no schema change.
- `schema_*`: apply schema change directly.
- `safe_*`: same operations, with idempotent checks first.

### Reference

| Function | What it does |
|---|---|
| `introspect_table_exists(db, table_name)` | Returns `True` if table exists. |
| `introspect_column_exists(db, table_name, column_name)` | Returns `True` if column exists. |
| `introspect_index_exists(db, index_name)` | Returns `True` if index exists. |
| `introspect_table_columns(db, table_name)` | Returns columns metadata from `PRAGMA table_info`. |
| `introspect_table_indexes(db, table_name)` | Returns indexes metadata from `PRAGMA index_list`. |
| `schema_rename_table(db, old_name, new_name)` | Renames a table. |
| `schema_add_column(db, table_name, column_name, column_type, ...)` | Adds a column with optional `NOT NULL` and SQL default. |
| `schema_rename_column(db, table_name, old_name, new_name)` | Renames a column. |
| `schema_drop_column(db, table_name, column_name)` | Drops a column (SQLite 3.35+). |
| `schema_create_index(db, table_name, column_names, ...)` | Creates an index and returns its name. |
| `schema_drop_index(db, index_name, ...)` | Drops an index by name. |
| `safe_rename_table(...)` | Renames only if old exists and new does not. |
| `safe_add_column(...)` | Adds only if column does not exist. |
| `safe_rename_column(...)` | Renames only if old exists and new does not. |
| `safe_drop_column(...)` | Drops only if column exists. |
| `safe_create_index(...)` | Creates only if index does not exist. |
| `safe_drop_index(...)` | Drops only if index exists. |

### Example: safe column rename

```python
from silly_engine.silly_orm.migration_helpers import safe_rename_column


def mig_2_0_0(db):
    safe_rename_column(db, "knights", "title", "rank")
```

### Example: add and drop index

```python
from silly_engine.silly_orm.migration_helpers import safe_create_index, safe_drop_index


def mig_2_1_0(db):
    safe_create_index(db, "knights", ["name"], index_name="idx_knights_name")
    safe_drop_index(db, "idx_knights_old_name")
```

### Extra notes

- `safe_*` helpers are recommended for replayable migrations.
- For SQLite versions `< 3.35`, `schema_drop_column` raises `SillyDbError`.
- On migration failure, SillyORM prints a soft-red warning to stderr indicating that SQLite DDL rollback may be partial and schema should be verified.

### Important SQLite behavior

With SQLite, some DDL operations (for example `ALTER TABLE ... ADD COLUMN`) can persist even when a migration fails afterwards.

That means you can end up with:

- schema changes already applied,
- but `_settings.version` not advanced.

This is why migrations should stay idempotent and use `safe_*` helpers whenever possible.