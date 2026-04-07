import pytest

from silly_engine.silly_orm.tools import SillyDbError


def test_oto_relation_resolution_and_relational_filter(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35, "sword_id": "s2"})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    swords.insert({"_id": "s2", "name": "Durandal", "length": 110})

    result = knights.filter(sword__name="Excalibur").all()

    assert [row.obj.name for row in result] == ["Arthur"]
    assert knights.get(_id="k1").obj.sword.obj.name == "Excalibur"
    assert swords.get(_id="s1").obj.owner.obj.name == "Arthur"


def test_oto_reverse_side_backfills_forward_side(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120, "owner_id": "k1"})

    knight = knights.get(_id="k1")
    sword = swords.get(_id="s1")

    assert knight.obj.sword.obj.name == "Excalibur"
    assert sword.obj.owner.obj.name == "Arthur"


def test_oto_update_clears_previous_one_to_one_assignment(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    swords.insert({"_id": "s2", "name": "Durandal", "length": 110})

    knights.update("k1", sword_id="s2")

    assert knights.get(_id="k1").obj.sword.obj.name == "Durandal"
    assert swords.get(_id="s1").obj.owner is None
    assert swords.get(_id="s2").obj.owner.obj.name == "Arthur"


def test_otm_and_mto_resolution_and_filters(orm_tables):
    _, knights, _, dragons, _ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
    dragons.insert({"_id": "d2", "name": "Fafnir", "age": 150, "killer_id": "k2"})

    knight = knights.filter(dragons_killed__name="Smaug").first()
    dragon = dragons.filter(killer__name="Lancelot").first()

    assert knight.obj.name == "Arthur"
    assert [item.obj.name for item in knights.get(_id="k1").obj.dragons_killed] == ["Smaug"]
    assert dragon.obj.name == "Fafnir"
    assert dragons.get(_id="d2").obj.killer.obj.name == "Lancelot"


def test_otm_payload_is_ignored_on_insert_and_update(orm_tables):
    db, knights, _, dragons, _ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "dragons_killed_ids": ["d1"]})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
    knights.update("k1", dragons_killed=["d2"])

    knight_columns = [
        row[1]
        for row in db.execute("PRAGMA table_info(knights)").fetchall()
    ]

    assert "dragons_killed_ids" not in knight_columns
    assert [item.obj.name for item in knights.get(_id="k1").obj.dragons_killed] == ["Smaug"]


def test_mtm_insert_populates_join_table_and_reverse_accessor(orm_tables):
    db, knights, _, _, princesses = orm_tables

    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    princesses.insert({"_id": "p2", "name": "Elaine", "age": 20})
    knights.insert({
        "_id": "k1",
        "name": "Arthur",
        "age": 40,
        "courted_princesses_ids": ["p1", "p2"],
    })

    join_rows = db.execute(
        "SELECT knights_id, courted_princesses_id FROM _mtm_courted_princesses__knights ORDER BY courted_princesses_id"
    ).fetchall()

    assert join_rows == [("k1", "p1"), ("k1", "p2")]
    assert [item.obj.name for item in knights.get(_id="k1").obj.courted_princesses] == ["Guenievre", "Elaine"]
    assert [item.obj.name for item in princesses.get(_id="p1").obj.suitors] == ["Arthur"]


def test_mtm_update_replaces_links_and_accepts_alias_key(orm_tables):
    db, knights, _, _, princesses = orm_tables

    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    princesses.insert({"_id": "p2", "name": "Elaine", "age": 20})
    princesses.insert({"_id": "p3", "name": "Isolde", "age": 19})
    knights.insert({
        "_id": "k1",
        "name": "Arthur",
        "age": 40,
        "courted_princesses_ids": ["p1", "p2"],
    })

    knights.update("k1", courted_princesses=["p2", "p3"])

    join_rows = db.execute(
        "SELECT knights_id, courted_princesses_id FROM _mtm_courted_princesses__knights ORDER BY courted_princesses_id"
    ).fetchall()

    assert join_rows == [("k1", "p2"), ("k1", "p3")]
    assert [item.obj.name for item in knights.get(_id="k1").obj.courted_princesses] == ["Elaine", "Isolde"]


def test_mtm_update_adds_links_when_record_started_without_relations(orm_tables):
    db, knights, _, _, princesses = orm_tables

    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})

    assert knights.get(_id="k1").obj.courted_princesses == []

    knights.update("k1", courted_princesses=["p1"])

    join_rows = db.execute(
        "SELECT knights_id, courted_princesses_id FROM _mtm_courted_princesses__knights ORDER BY courted_princesses_id"
    ).fetchall()

    assert join_rows == [("k1", "p1")]
    assert [item.obj.name for item in knights.get(_id="k1").obj.courted_princesses] == ["Guenievre"]
    assert [item.obj.name for item in princesses.get(_id="p1").obj.suitors] == ["Arthur"]


def test_mtm_relational_filter_works_with_gt_operator(orm_tables):
    _, knights, _, _, princesses = orm_tables

    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    princesses.insert({"_id": "p2", "name": "Elaine", "age": 17})
    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "courted_princesses_ids": ["p1"]})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35, "courted_princesses_ids": ["p2"]})

    rows = knights.filter(courted_princesses__age__gt=18).all()

    assert [row.obj.name for row in rows] == ["Arthur"]


def test_duplicate_mtm_ids_are_ignored(orm_tables):
    db, knights, _, _, princesses = orm_tables

    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    knights.insert({
        "_id": "k1",
        "name": "Arthur",
        "age": 40,
        "courted_princesses_ids": ["p1", "p1", "p1"],
    })

    count = db.execute(
        "SELECT COUNT(*) FROM _mtm_courted_princesses__knights WHERE knights_id='k1' AND courted_princesses_id='p1'"
    ).fetchone()[0]

    assert count == 1


def test_invalid_mtm_payload_type_raises(orm_tables):
    _, knights, *_ = orm_tables

    with pytest.raises(SillyDbError, match="Unsupported MTM value type"):
        knights.insert({
            "_id": "k1",
            "name": "Arthur",
            "age": 40,
            "courted_princesses_ids": 123,
        })
