from silly_engine.jsondb import JsonDb


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


def test_jsondb_migrations(tmp_path):
    dbfile = tmp_path / 'db.json'

    # Create an initial database with version 1.0.0
    db = JsonDb(str(dbfile), autosave=False, version="1.0.0")
    coll = db.collection('test')
    coll.insert({'name': 'alice', 'age': 20})
    db.save()

    # Define a migration that adds a 'migrated' field to all items
    def migration_1_1_0(db):
        coll = db.collection('test')
        for item in coll.all():
            item.data['migrated'] = True

    migrations = {
        "1.1.0": migration_1_1_0
    }

    # Reload the database with the migration and a higher version
    db2 = JsonDb(str(dbfile), autosave=False, version="1.1.0", migrations=migrations)
    coll2 = db2.collection('test')
    items = list(coll2.all())
    assert len(items) == 1
    assert items[0].data['name'] == 'alice'
    assert items[0].data['migrated'] is True
