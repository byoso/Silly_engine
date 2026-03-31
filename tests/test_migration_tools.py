from dataclasses import dataclass
import random
from typing import Any

from silly_engine import (
    SillyDb,
    ValidatedWithId,
    Oto,
)


def test_chained_rename_and_remove_migrations():
    db = SillyDb(":memory:")

    @dataclass
    class Castle(ValidatedWithId):
        name: str = ""
        location: str = ""
        color: str = ""
        archers: int = 0
        owner_id: Oto | Any = Oto(target="knights")

    Castles = db.table("castles", Castle)
    Castles.delete_all()

    # populate a few rows
    for i in range(3):
        c = Castle(name=f"C{i}", location="L", color="Red", archers=10 + i)
        Castles.save(c)

    from silly_engine.silly_db import rename_field, remove_field

    def mig_1_0_0(db_local: SillyDb) -> None:
        rename_field(db_local, "castles", "archers", "defenders")

    def mig_1_1_0(db_local: SillyDb) -> None:
        remove_field(db_local, "castles", "color")

    # apply migrations in order
    db.migrate([
        ("1.0.0", mig_1_0_0),
        ("1.1.0", mig_1_1_0),
    ])

    # inspect final table columns
    with db._transaction():
        db.cursor.execute("PRAGMA table_info(castles)")
        cols = [r[1] for r in db.cursor.fetchall()]

    # Expected: 'archers' removed (renamed to 'defenders'), 'color' removed, and 'defenders' present
    assert "archers" not in cols, f"Unexpected column 'archers' present after migrations: {cols}"
    assert "color" not in cols, f"Unexpected column 'color' present after migrations: {cols}"
    assert "defenders" in cols, f"Renamed column 'defenders' not present after migrations: {cols}"


def test_rename_table_simple_and_target_exists():
    db = SillyDb(":memory:")

    @dataclass
    class Castle(ValidatedWithId):
        name: str = ""
        location: str = ""
        color: str = ""
        archers: int = 0
        owner_id: Oto | Any = Oto(target="knights")

    # simple rename when destination does not exist
    Castles = db.table("castles", Castle)
    Castles.delete_all()
    for i in range(3):
        Castles.save(Castle(name=f"C{i}", location="L", color="Red", archers=5 + i))

    from silly_engine.silly_db import rename_table, rename_field, remove_field

    rename_table(db, "castles", "manors")
    # ensure registry updated and data preserved
    assert "castles" not in db.tables
    assert "manors" in db.tables
    Manors = db.tables["manors"]
    rows = Manors.get_all()
    assert len(rows) == 3

    # target exists case: create a new source and existing dest
    # recreate source
    Castles2 = db.table("castles", Castle)
    Castles2.delete_all()
    for i in range(2):
        Castles2.save(Castle(name=f"X{i}", location="LX", color="Blue", archers=10 + i))
    # create destination with one row
    Manors2 = db.table("manors", Castle)
    Manors2.save(Castle(name="Existing", location="E", color="Green", archers=99))

    # now rename 'castles' into existing 'manors' — should append common columns
    rename_table(db, "castles", "manors")
    # manors should contain previous manors + castles2 rows
    total = Manors2.get_all()
    assert len(total) >= 3


def test_rename_field_when_new_exists_and_remove_field():
    db = SillyDb(":memory:")

    @dataclass
    class Castle2(ValidatedWithId):
        name: str = ""
        location: str = ""
        color: str = ""
        archers: int = 0
        defenders: int = 0

    Castles = db.table("castles2", Castle2)
    Castles.delete_all()
    # create rows where 'archers' has values and 'defenders' is left default (0)
    Castles.save(Castle2(name="A", location="L", color="C", archers=7))
    Castles.save(Castle2(name="B", location="L", color="C", archers=11))

    from silly_engine.silly_db import rename_field, remove_field

    # rename archers -> defenders: defenders column exists so values should be copied and archers removed
    rename_field(db, "castles2", "archers", "defenders")
    with db._transaction():
        db.cursor.execute("PRAGMA table_info(castles2)")
        cols = [r[1] for r in db.cursor.fetchall()]
    assert "archers" not in cols
    assert "defenders" in cols

    # now test remove_field: remove the 'color' column
    remove_field(db, "castles2", "color")
    with db._transaction():
        db.cursor.execute("PRAGMA table_info(castles2)")
        cols2 = [r[1] for r in db.cursor.fetchall()]
    assert "color" not in cols2
