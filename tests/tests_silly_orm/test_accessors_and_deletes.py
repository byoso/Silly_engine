def test_accessor_add_remove_updates_all_relation_types(orm_tables):
    _, knights, swords, dragons, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": None})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})

    arthur = knights.filter_first(_id="k1")
    guenievre = princesses.filter_first(_id="p1")

    arthur.q.sword.add("s1")
    arthur.q.dragons_killed.add("d1")
    arthur.q.courted_princesses.add(guenievre)

    arthur = knights.filter_first(_id="k1")
    assert arthur.q.sword.q.name == "Excalibur"
    assert [item.q.name for item in arthur.q.dragons_killed] == ["Smaug"]
    assert [item.q.name for item in arthur.q.courted_princesses] == ["Guenievre"]

    arthur.q.courted_princesses.remove(guenievre)
    arthur.q.dragons_killed.remove("d1")
    arthur.q.sword.remove()

    arthur = knights.filter_first(_id="k1")
    assert arthur.q.sword.get() is None
    assert arthur.q.dragons_killed.to_list() == []
    assert arthur.q.courted_princesses.to_list() == []


def test_accessor_relation_mutator_fluent_api(orm_tables):
    _, knights, _, _, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
    princess = princesses.filter_first(_id="p1")

    knight = knights.filter_first(_id="k1")
    knight.q.courted_princesses.add(princess)
    knight.q.courted_princesses.remove(princess)

    knight = knights.filter_first(_id="k1")
    assert knight.q.courted_princesses.to_list() == []


def test_accessor_exposes_model_property(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})

    arthur = knights.filter_first(_id="k1")
    assert arthur is not None
    assert arthur.q.label == "Arthur (40)"
    assert arthur.q.has_sword is False


def test_accessor_property_is_refreshed_after_relation_mutation(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})

    arthur = knights.filter_first(_id="k1")
    assert arthur is not None
    assert arthur.q.has_sword is False

    arthur.q.sword.add("s1")
    assert arthur.q.has_sword is True

    arthur.q.sword.remove()
    assert arthur.q.has_sword is False


def test_delete_by_id_cleans_oto_mto_and_mtm_relations(orm_tables):
    db, knights, swords, dragons, princesses = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1", "courted_princesses_ids": ["p1"]})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
    princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})

    knights.delete_by_id("k1")

    assert knights.filter_first(_id="k1") is None
    assert swords.filter_first(_id="s1").q.owner.get() is None
    assert dragons.filter_first(_id="d1").q.killer.get() is None
    remaining_links = db.execute(
        "SELECT COUNT(*) FROM _mtm_courted_princesses__knights WHERE knights_id='k1'"
    ).fetchone()[0]
    assert remaining_links == 0


def test_delete_by_id_clears_forward_oto_reference_when_target_deleted(orm_tables):
    _, knights, swords, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})

    swords.delete_by_id("s1")

    knight = knights.filter_first(_id="k1")
    assert knight is not None
    assert knight.q.sword.get() is None
