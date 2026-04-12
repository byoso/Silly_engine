[jsondb index](00_jsondb_index.md)

# Versioning and migrations

JsonDb can run migration functions based on semantic versions.

## Migration setup

```python
from silly_engine.jsondb import JsonDb


def mig_1_0_0(db: JsonDb):
    queries = db.collection("queries")
    for item in queries.all():
        item.update({"migrated": True})


def mig_2_0_0(db: JsonDb):
    queries = db.collection("queries")
    for item in queries.all():
        data = item.data
        if data.get("foo") is not None:
            data["name"] = data.pop("foo")
            item.update(data)


db = JsonDb(
    "data.json",
    autosave=True,
    version="2.0.0",
    migrations={
        "1.0.0": mig_1_0_0,
        "2.0.0": mig_2_0_0,
    },
)
```

## Rules

- migration keys use x.y.z strings
- each migration receives the db instance
- _settings.version is updated after each successful migration

## Notes

- Version objects support comparison operators
- malformed versions raise JsonDbError
