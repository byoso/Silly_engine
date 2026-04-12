[jsondb index](00_jsondb_index.md)

# JsonDb introduction

JsonDb is a lightweight JSON-file database with collections, item wrappers, and optional versioned migrations.

## Quick start

```python
from silly_engine.jsondb import JsonDb

# autosave=False means you control when to flush to disk
db = JsonDb("data.json", autosave=False, version="1.0.0")
people = db.collection("people")

alice = people.insert({"name": "Alice", "age": 30})
print(alice.data)

rows = people.filter(lambda x: x["age"] >= 18)
print([row.data["name"] for row in rows])

db.save()
```

## Main concepts

- JsonDb: database object attached to one JSON file
- Collection: named container of items
- Item: wrapper around one record with helpers
- _settings: internal singleton-like collection used for version tracking

## Related pages

- [02 Collection CRUD](02_Collection_CRUD.md)
- [03 Versioning and Migrations](03_Versioning_and_Migrations.md)
