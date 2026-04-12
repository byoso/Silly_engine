import json


def test_qitem_dict_and_json(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    arthur = knights.get(_id="k1")

    d = arthur.dict()
    assert isinstance(d, dict)
    assert d["_id"] == "k1"
    assert d["name"] == "Arthur"
    assert d["age"] == 40

    j = arthur.json()
    assert isinstance(j, str)
    parsed = json.loads(j)
    assert parsed["_id"] == "k1"
    assert parsed["name"] == "Arthur"


def test_query_dict_returns_list_of_dicts(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})

    results = knights.filter(age__gt=30).dict()
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(r, dict) for r in results)
    assert results[0]["name"] in ["Arthur", "Lancelot"]


def test_query_json_returns_json_string(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})

    j = knights.filter(age__gt=30).json()
    assert isinstance(j, str)
    parsed = json.loads(j)
    assert len(parsed) == 2
    assert parsed[0]["name"] in ["Arthur", "Lancelot"]


def test_pagination_basic(orm_tables):
    _, knights, *_ = orm_tables

    for i in range(1, 11):
        knights.insert({"_id": f"k{i}", "name": f"Knight{i}", "age": 30 + i})

    page1 = knights.filter().paginate(page_size=3, page=1)
    assert page1.page == 1
    assert page1.page_size == 3
    assert page1.total == 10
    assert len(page1.data) == 3

    page2 = knights.filter().paginate(page_size=3, page=2)
    assert page2.page == 2
    assert len(page2.data) == 3
    assert page2.data[0].q._id != page1.data[0].q._id

    page4 = knights.filter().paginate(page_size=3, page=4)
    assert page4.page == 4
    assert len(page4.data) == 1

    page5 = knights.filter().paginate(page_size=3, page=5)
    assert len(page5.data) == 0


def test_pagination_with_filters(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Young1", "age": 20})
    knights.insert({"_id": "k2", "name": "Young2", "age": 22})
    knights.insert({"_id": "k3", "name": "Old1", "age": 50})
    knights.insert({"_id": "k4", "name": "Old2", "age": 55})
    knights.insert({"_id": "k5", "name": "Old3", "age": 60})

    page = knights.filter(age__gte=50).paginate(page_size=2, page=1)
    assert page.total == 3
    assert len(page.data) == 2

    page2 = knights.filter(age__gte=50).paginate(page_size=2, page=2)
    assert len(page2.data) == 1


def test_pagination_dict_conversion(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})

    page = knights.filter().paginate(page_size=1, page=1)
    page_dict = page.dict()

    assert isinstance(page_dict, dict)
    assert "data" in page_dict
    assert "page" in page_dict
    assert "page_size" in page_dict
    assert "total" in page_dict
    assert isinstance(page_dict["data"], list)
    assert isinstance(page_dict["data"][0], dict)


def test_pagination_json_conversion(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})

    page = knights.filter().paginate(page_size=10, page=1)
    j = page.json()

    assert isinstance(j, str)
    parsed = json.loads(j)
    assert parsed["page"] == 1
    assert parsed["page_size"] == 10
    assert parsed["total"] == 1
    assert len(parsed["data"]) == 1


def test_count_on_table_no_filter(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    total = knights.count()
    assert total == 3


def test_count_with_filters(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    young = knights.filter(age__lt=35).count()
    assert young == 1

    old = knights.filter(age__gte=35).count()
    assert old == 2


def test_count_chainable_on_query(orm_tables):
    _, knights, *_ = orm_tables

    knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
    knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
    knights.insert({"_id": "k3", "name": "Perceval", "age": 25})

    count = knights.filter(age__gte=30).order_by("age").count()
    assert count == 2

    zero = knights.filter(age__gt=100).count()
    assert zero == 0
