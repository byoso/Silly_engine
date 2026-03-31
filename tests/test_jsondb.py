import json
import os

from silly_engine.jsondb import Version, JsonDb


def test_version_parsing_and_comparison():
    v1 = Version('1.2.3')
    v2 = Version('1.3.0')
    assert str(v1) == '1.2.3'
    assert v1 < v2
    assert v2 > v1


def test_collection_insert_get_update_delete(tmp_path):
    dbfile = tmp_path / 'db.json'
    db = JsonDb(str(dbfile), autosave=False)
    coll = db.collection('test')
    item = coll.insert({'name': 'alice'})
    assert coll.get(item._id).data['name'] == 'alice'
    item.set(('age', 20))
    assert item.data['age'] == 20
    item.update({'name': 'bob'})
    assert item.data['name'] == 'bob'
    item.del_attr('age')
    assert 'age' not in item.data
    item.delete()
    assert coll.get(item._id) is None
