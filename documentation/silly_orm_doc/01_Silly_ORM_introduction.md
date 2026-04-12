[silly_orm index](00_silly_orm_index.md)

# Silly ORM introduction

`Silly_ORM` is a lightweight ORM for local SQL projects.

It gives you:

- Dataclass-based models
- Simple table registration (`db.table(...)`)
- CRUD helpers (`insert`, `update`, `delete`, `filter`)
- Built-in relations (`Oto`, `Mto`, `Otm`, `Mtm`)
- Versioned function-based migrations (`db.migrate([...])`)
- Atomic transactions with rollback on errors

In short: you write Python objects, `Silly_ORM` handles SQL and relation wiring with minimal setup.

## Feature pages

- [03 Dataclass models](03_Dataclass_models.md)
- [04 Table registration](04_Table_registration.md)
- [05 CRUD helpers](05_CRUD_helpers.md)
- [06 Relations](06_Relations.md)
- [07 Migrations](07_Migrations.md)
- [08 Transactions](08_Transactions.md)
- [09 Backend agnostic](09_Backend_agnostic.md)

## Quick start

```python
from dataclasses import dataclass
from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.models import Model
from silly_engine.silly_orm.relations import Oto

# declare your models
@dataclass
class Knight(Model):
	name: str
	age: int
	sword: Oto = Oto("swords")


@dataclass
class Sword(Model):
	name: str
	length: int
	owner: Oto = Oto("knights")

# declare the database and registe the models
db = SillyDb("DB.sqlite3")
Knights = db.table("knights", Knight)
Swords = db.table("swords", Sword)

# your app can do some stuff:
Swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
Knights.insert({"name": "Arthur", "age": 40, "sword": "s1"})

arthur = Knights.filter(name="Arthur").first()
print(arthur.q.name, "uses", arthur.q.sword.q.name)
```
