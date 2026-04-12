def test_insert_without_id_generates_uuid_and_get_returns_qitem(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"name": "Arthur", "age": 40})

    knight = knights.get(name="Arthur")
    assert knight is not None
    assert isinstance(knight._data["_id"], str)
    assert knight._data["_id"]
    assert repr(knight).startswith("<QKnight ")


def test_simple_filter_order_and_limit(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Gawain", "age": 50})

    rows = knights.filter(age__gt=35).order_by("-age").limit(2).all()

    assert [row.q.name for row in rows] == ["Gawain", "Arthur"]
    assert knights.filter(name="Lancelot").first().q.age == 35


def test_update_scalar_fields(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.update("k1", age=41, name="Arthur Pendragon")

    knight = knights.get(_id="k1")
    assert knight.q.name == "Arthur Pendragon"
    assert knight.q.age == 41


def test_query_iter_equals_all(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    query = knights.filter(age__gt=30).order_by("age")
    via_all = query.all()
    via_iter = list(knights.filter(age__gt=30).order_by("age"))

    assert [item._data["_id"] for item in via_all] == [item._data["_id"] for item in via_iter]


def test_bulk_update_with_filter_chain(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    affected = knights.update(name="Veteran").filter(age__gte=35).execute()

    assert affected == 2
    assert knights.filter(name="Veteran").count() == 2
    assert knights.get(_id="k3").q.name == "Perceval"


def test_bulk_update_apply_alias(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    affected = knights.update(name="Senior").filter(age__gte=35).apply()

    assert affected == 2
    assert knights.filter(name="Senior").count() == 2
    assert knights.get(_id="k3").q.name == "Perceval"


def test_bulk_delete_with_relational_filter_chain(orm_tables):
    _, knights, swords, *_ = orm_tables

    swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
    swords.insert({"_id": "s2", "name": "Durandal", "length": 110})

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35, "sword_id": "s2"})

    affected = knights.delete().filter(sword__name="Excalibur").execute()

    assert affected == 1
    assert knights.get(_id="k1") is None
    assert knights.get(_id="k2") is not None
