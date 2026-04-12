def test_accessor_add_remove_updates_all_relation_types(orm_tables):
    _, knights, swords, dragons, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": None})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})

    arthur = knights.get(_id="k1")
    guenievre = princesses.get(_id="p1")

    arthur.q.add("sword", "s1")
    arthur.q.add("dragons_killed", "d1")
    arthur.q.add("courted_princesses", guenievre)

    arthur = knights.get(_id="k1")
    assert arthur.q.sword.q.name == "Excalibur"
    assert [item.q.name for item in arthur.q.dragons_killed] == ["Smaug"]
    assert [item.q.name for item in arthur.q.courted_princesses] == ["Guenievre"]

    arthur.q.remove("courted_princesses", guenievre)
    arthur.q.remove("dragons_killed", "d1")
    arthur.q.remove("sword")

    arthur = knights.get(_id="k1")
    assert arthur.q.sword is None
    assert arthur.q.dragons_killed == []
    assert arthur.q.courted_princesses == []


def test_accessor_relation_mutator_fluent_api(orm_tables):
    _, knights, _, _, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    princess = princesses.get(_id="p1")

    knight = knights.get(_id="k1")
    knight.q.relation("courted_princesses").add(princess)
    knight.q.relation("courted_princesses").remove(princess)

    knight = knights.get(_id="k1")
    assert knight.q.courted_princesses == []


def test_delete_by_id_cleans_oto_mto_and_mtm_relations(orm_tables):
    db, knights, swords, dragons, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1", "courted_princesses_ids": ["p1"]})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})

    knights.delete_by_id("k1")

    assert knights.get(_id="k1") is None
    assert swords.get(_id="s1").q.owner is None
    assert dragons.get(_id="d1").q.killer is None
    remaining_links = db.execute(
        "SELECT COUNT(*) FROM _mtm_courted_princesses__knights WHERE knights_id='k1'"
    ).fetchone()[0]
    assert remaining_links == 0


def test_delete_by_id_clears_forward_oto_reference_when_target_deleted(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})

    swords.delete_by_id("s1")

    knight = knights.get(_id="k1")
    assert knight is not None
    assert knight.q.sword is None
