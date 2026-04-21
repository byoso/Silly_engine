import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.migration_helpers import (
    introspect_column_exists,
    introspect_index_exists,
    introspect_table_exists,
    safe_add_column,
    safe_create_index,
    safe_rename_column,
    safe_rename_table,
)


def test_migrate_applies_helper_based_schema_changes_and_updates_version():
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE knights (_id TEXT PRIMARY KEY, name TEXT)")
    db.execute("INSERT INTO knights (_id, name) VALUES (?, ?)", ("k1", "Arthur"))

    def mig_1_0_0(migration_db):
        safe_add_column(migration_db, "knights", "rank", "TEXT", default_sql="'Squire'")

    def mig_1_1_0(migration_db):
        safe_rename_column(migration_db, "knights", "rank", "title")

    def mig_1_2_0(migration_db):
        safe_create_index(migration_db, "knights", ["title"], index_name="idx_knights_title")

    db.migrate({
        "1.0.0": mig_1_0_0,
        "1.1.0": mig_1_1_0,
        "1.2.0": mig_1_2_0,
    })

    assert introspect_column_exists(db, "knights", "rank") is False
    assert introspect_column_exists(db, "knights", "title") is True
    assert introspect_index_exists(db, "idx_knights_title") is True

    db.execute("SELECT title FROM knights WHERE _id=?", ("k1",))
    assert db.fetchone()[0] == "Squire"

    settings = db.table("_settings").first()
    assert settings is not None
    assert settings.q.version == "1.2.0"



def test_migrate_does_not_reapply_same_versions():
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE migration_runs (_id TEXT PRIMARY KEY, value TEXT)")

    counters = {"a": 0, "b": 0}

    def mig_1_0_0(migration_db):
        counters["a"] += 1
        migration_db.execute("INSERT INTO migration_runs (_id, value) VALUES (?, ?)", ("a", "v1"))

    def mig_1_1_0(migration_db):
        counters["b"] += 1
        migration_db.execute("INSERT INTO migration_runs (_id, value) VALUES (?, ?)", ("b", "v2"))

    migrations = {
        "1.0.0": mig_1_0_0,
        "1.1.0": mig_1_1_0,
    }

    db.migrate(migrations)
    db.migrate(migrations)

    assert counters == {"a": 1, "b": 1}

    db.execute("SELECT _id FROM migration_runs ORDER BY _id")
    assert db.fetchall() == [("a",), ("b",)]

    settings = db.table("_settings").first()
    assert settings is not None
    assert settings.q.version == "1.1.0"



def test_migrate_rename_table_with_safe_helper():
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE warriors (_id TEXT PRIMARY KEY, name TEXT)")

    def mig_2_0_0(migration_db):
        safe_rename_table(migration_db, "warriors", "knights")

    db.migrate({"2.0.0": mig_2_0_0})

    assert introspect_table_exists(db, "warriors") is False
    assert introspect_table_exists(db, "knights") is True

    settings = db.table("_settings").first()
    assert settings is not None
    assert settings.q.version == "2.0.0"


def test_migrate_failed_helper_migration_does_not_advance_db_version():
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE knights (_id TEXT PRIMARY KEY, name TEXT)")

    def mig_3_0_0(migration_db):
        safe_add_column(migration_db, "knights", "rank", "TEXT", default_sql="'Squire'")
        raise RuntimeError("boom")

    with pytest.raises(Exception):
        db.migrate({"3.0.0": mig_3_0_0})

    # SQLite may persist ALTER TABLE schema changes even when migration fails.
    assert introspect_column_exists(db, "knights", "rank") is True

    settings = db.table("_settings").first()
    assert settings is not None
    assert settings.q.version == "0.0.0"
