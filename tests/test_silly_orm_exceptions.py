from dataclasses import dataclass

import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.models import Model
from silly_engine.silly_orm.relations import Mtm
from silly_engine.silly_orm.tools import SillyDbError


@dataclass
class Knight(Model):
    name: str
    courted_princesses_ids: Mtm | None = Mtm("princesses")


@dataclass
class Princess(Model):
    name: str
    suitors_ids: Mtm | None = Mtm("knights")


@dataclass
class GuardedKnight(Model):
    name: str
    age: int

    @classmethod
    def validate(cls, payload: dict, operation: str = "insert", record_id: str | None = None):
        if payload.get("age") is not None and payload["age"] < 0:
            raise SillyDbError("age must be >= 0")


def test_table_requires_model_raises_silly_db_error():
    db = SillyDb(":memory:")
    with pytest.raises(SillyDbError):
        db.table("missing_model")


def test_invalid_mtm_payload_type_raises_silly_db_error():
    db = SillyDb(":memory:")
    knights = db.table("knights", Knight)
    db.table("princesses", Princess)

    with pytest.raises(SillyDbError):
        knights.insert({"_id": "k1", "name": "Arthur", "courted_princesses_ids": 123})


def test_unknown_relation_filter_raises_silly_db_error():
    db = SillyDb(":memory:")
    knights = db.table("knights", Knight)

    with pytest.raises(SillyDbError):
        knights.filter(unknown_rel__name="x").all()


def test_model_validate_hook_blocks_invalid_insert():
    db = SillyDb(":memory:")
    knights = db.table("guarded_knights", GuardedKnight)

    with pytest.raises(SillyDbError, match="age must be >= 0"):
        knights.insert({"_id": "k1", "name": "Arthur", "age": -1})

    assert knights.count() == 0


def test_model_validate_hook_blocks_invalid_update():
    db = SillyDb(":memory:")
    knights = db.table("guarded_knights", GuardedKnight)

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})

    with pytest.raises(SillyDbError, match="age must be >= 0"):
        knights.update("k1", age=-2)

    assert knights.get(_id="k1").obj.age == 40


def test_failed_migration_raises_silly_db_error_and_rolls_back_version(capsys):
    db = SillyDb(":memory:")
    db.execute("CREATE TABLE migration_rows (_id TEXT PRIMARY KEY, name TEXT)")

    def mig_ok(migration_db):
        migration_db.execute("INSERT INTO migration_rows (_id, name) VALUES (?, ?)", ("1", "ok"))

    def mig_bad(migration_db):
        migration_db.execute("INSERT INTO migration_rows (_id, name) VALUES (?, ?)", ("2", "bad"))
        raise RuntimeError("boom")

    with pytest.raises(SillyDbError):
        db.migrate([
            ("1.0.0", mig_ok),
            ("1.1.0", mig_bad),
        ])

    captured = capsys.readouterr()
    assert "SQLite DDL rollback may be partial" in captured.err

    settings = db.table("_settings").first()
    assert settings is not None
    assert settings.obj.version == "1.0.0"

    rows = db.execute("SELECT _id FROM migration_rows ORDER BY _id").fetchall()
    assert rows == [("1",)]
