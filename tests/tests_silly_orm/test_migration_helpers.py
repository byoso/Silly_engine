import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.migration_helpers import (
    introspect_column_exists,
    introspect_index_exists,
    introspect_table_columns,
    introspect_table_exists,
    introspect_table_indexes,
    make_index_name,
    quote_identifier,
    raw_sql_migration,
    safe_add_column,
    safe_create_index,
    safe_drop_column,
    safe_drop_index,
    safe_rename_column,
    safe_rename_table,
    schema_add_column,
    schema_create_index,
    schema_drop_column,
    schema_drop_index,
    schema_rename_column,
    schema_rename_table,
)
from silly_engine.silly_orm.tools import SillyDbError


@pytest.fixture
def db():
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE knights (_id TEXT PRIMARY KEY, name TEXT)")
    try:
        yield db
    finally:
        db.close()


def test_quote_identifier_escapes_double_quotes():
    assert quote_identifier('a"b') == '"a""b"'


def test_make_index_name_builds_deterministic_name():
    assert make_index_name("knights", ["name", "age"]) == "idx_knights_name_age"


def test_raw_sql_migration_executes_statement(db):
    raw_sql_migration(db, "INSERT INTO knights (_id, name) VALUES (?, ?)", ("k1", "Arthur"))
    db.execute("SELECT name FROM knights WHERE _id=?", ("k1",))
    assert db.fetchone()[0] == "Arthur"


def test_introspect_helpers_table_and_column(db):
    assert introspect_table_exists(db, "knights") is True
    assert introspect_table_exists(db, "missing") is False
    assert introspect_column_exists(db, "knights", "name") is True
    assert introspect_column_exists(db, "knights", "age") is False


def test_introspect_table_columns_returns_expected_shape(db):
    columns = introspect_table_columns(db, "knights")
    names = [c["name"] for c in columns]
    assert "_id" in names
    assert "name" in names


def test_schema_add_and_rename_column(db):
    schema_add_column(db, "knights", "title", "TEXT", default_sql="'Sir'")
    assert introspect_column_exists(db, "knights", "title") is True

    schema_rename_column(db, "knights", "title", "rank")
    assert introspect_column_exists(db, "knights", "title") is False
    assert introspect_column_exists(db, "knights", "rank") is True


def test_schema_rename_table(db):
    schema_rename_table(db, "knights", "warriors")
    assert introspect_table_exists(db, "knights") is False
    assert introspect_table_exists(db, "warriors") is True


def test_schema_create_and_drop_index(db):
    idx_name = schema_create_index(db, "knights", ["name"])
    assert introspect_index_exists(db, idx_name) is True

    table_indexes = introspect_table_indexes(db, "knights")
    names = [idx["name"] for idx in table_indexes]
    assert idx_name in names

    schema_drop_index(db, idx_name)
    assert introspect_index_exists(db, idx_name) is False


def test_schema_create_index_requires_at_least_one_column(db):
    with pytest.raises(SillyDbError, match="at least one column"):
        schema_create_index(db, "knights", [])


def test_safe_add_column_is_idempotent(db):
    assert safe_add_column(db, "knights", "age", "INTEGER") is True
    assert safe_add_column(db, "knights", "age", "INTEGER") is False


def test_safe_rename_column_guards_preconditions(db):
    assert safe_rename_column(db, "knights", "missing", "x") is False
    assert safe_rename_column(db, "knights", "name", "_id") is False

    assert safe_rename_column(db, "knights", "name", "full_name") is True
    assert introspect_column_exists(db, "knights", "full_name") is True


def test_safe_create_and_drop_index(db):
    name = safe_create_index(db, "knights", ["name"], index_name="idx_knights_name")
    assert name == "idx_knights_name"
    assert safe_create_index(db, "knights", ["name"], index_name="idx_knights_name") is None

    assert safe_drop_index(db, "idx_knights_name") is True
    assert safe_drop_index(db, "idx_knights_name") is False


def test_safe_rename_table_guards_preconditions(db):
    db.execute("CREATE TABLE wizards (_id TEXT PRIMARY KEY)")

    assert safe_rename_table(db, "missing", "new_name") is False
    assert safe_rename_table(db, "knights", "wizards") is False
    assert safe_rename_table(db, "knights", "warriors") is True


def test_schema_drop_column_version_guard(monkeypatch, db):
    schema_add_column(db, "knights", "temp_col", "TEXT")

    import silly_engine.silly_orm.migration_helpers as mh

    monkeypatch.setattr(mh, "_sqlite_version_tuple", lambda _: (3, 34, 0))
    with pytest.raises(SillyDbError, match="requires SQLite >= 3.35.0"):
        schema_drop_column(db, "knights", "temp_col")


def test_safe_drop_column_when_missing_returns_false(db):
    assert safe_drop_column(db, "knights", "missing") is False
