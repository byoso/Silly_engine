import os
from dataclasses import dataclass
from uuid import uuid4

import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.migration_helpers import (
    introspect_column_exists,
    introspect_index_exists,
    introspect_table_exists,
    safe_add_column,
    safe_create_index,
    safe_rename_column,
)
from silly_engine.silly_orm.models import Model


pytestmark = pytest.mark.postgres


def _uniq(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


@pytest.fixture
def pg_db():
    pytest.importorskip("psycopg2")
    dsn = os.getenv("TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TEST_POSTGRES_DSN not set; skipping postgres integration tests.")

    from silly_engine.silly_orm.connectors.postgres import PostgresConnector

    db = SillyDb(connector=PostgresConnector(dsn))
    try:
        yield db
    finally:
        db.close()


def test_postgres_table_creation_and_basic_insert(pg_db):
    table_name = _uniq("pg_knights")

    pg_db.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (_id TEXT PRIMARY KEY, name TEXT)")
    pg_db.execute(f"INSERT INTO {table_name} (_id, name) VALUES (?, ?)", ("k1", "Arthur"))
    pg_db.execute(f"SELECT name FROM {table_name} WHERE _id=?", ("k1",))

    assert pg_db.fetchone()[0] == "Arthur"

    pg_db.execute(f"DROP TABLE IF EXISTS {table_name}")


def test_postgres_migration_helpers_introspection_and_safe_ops(pg_db):
    table_name = _uniq("pg_helpers")

    pg_db.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (_id TEXT PRIMARY KEY, name TEXT)")

    assert introspect_table_exists(pg_db, table_name) is True
    assert introspect_column_exists(pg_db, table_name, "nickname") is False

    assert safe_add_column(pg_db, table_name, "nickname", "TEXT") is True
    assert introspect_column_exists(pg_db, table_name, "nickname") is True

    assert safe_rename_column(pg_db, table_name, "nickname", "alias") is True
    assert introspect_column_exists(pg_db, table_name, "alias") is True

    idx = safe_create_index(pg_db, table_name, ["alias"])
    assert idx is not None
    assert introspect_index_exists(pg_db, idx) is True

    pg_db.execute(f"DROP TABLE IF EXISTS {table_name}")


def test_postgres_generate_schema_uses_boolean_and_bigint(pg_db):
    table_name = _uniq("pg_model")

    @dataclass
    class Event(Model):
        name: str
        active: bool

        class Meta:
            auto_now_add = True
            auto_now = True
            ttl = 60

    events = pg_db.table(table_name, Event)
    events.insert({"name": "hello", "active": True})

    # Verify schema types through information_schema.
    pg_db.execute(
        "SELECT column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = ?",
        (table_name,),
    )
    type_by_col = {row[0]: row[1] for row in pg_db.fetchall()}

    assert type_by_col["active"] == "boolean"
    assert type_by_col["_created_at"] == "bigint"
    assert type_by_col["_updated_at"] == "bigint"
    assert type_by_col["_expires_at"] == "bigint"

    pg_db.execute(f"DROP TABLE IF EXISTS {table_name}")
