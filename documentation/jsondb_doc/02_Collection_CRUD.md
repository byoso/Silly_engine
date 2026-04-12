[jsondb index](00_jsondb_index.md)

# Collection CRUD

Collection provides insert/get/update/delete plus query helpers.

## Basic operations

```python
from silly_engine.jsondb import JsonDb

db = JsonDb("data.json", autosave=False)
items = db.collection("items")

created = items.insert({"name": "sword", "power": 10})
key = created._id

loaded = items.get(key)
loaded.set(("power", 12))
loaded.update({"name": "Excalibur"})
loaded.del_attr("unused")

subset = items.filter(lambda x: x.get("power", 0) >= 10)
removed_ids = items.filter_delete(lambda x: x.get("power", 0) < 5)

items.delete(key)
```

## Dataclass output models

You can pass a dataclass model when creating a collection.

```python
from dataclasses import dataclass
from silly_engine.jsondb import JsonDb

@dataclass
class Person:
    _id: str
    name: str
    age: int

db = JsonDb("data.json")
people = db.collection("people", model=Person)
person = people.insert({"name": "Bob", "age": 42})
print(person.name)
```

## Notes

- insert() ignores an input _id key and manages ids internally
- first() and first_update() are useful for singleton-style collections
