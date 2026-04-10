[silly_orm index](00_silly_orm_index.md)

# Relations

Silly ORM supports four relation types:

- `Oto`: one-to-one
- `Mto`: many-to-one
- `Otm`: one-to-many
- `Mtm`: many-to-many

## Example models

```python
from dataclasses import dataclass
from silly_engine.silly_orm.models import Model
from silly_engine.silly_orm.relations import Oto, Mto, Otm, Mtm


@dataclass
class Knight(Model):
    name: str
    age: int
    sword_id: Oto = Oto("swords")
    dragons_killed_ids: Otm = Otm("dead_dragons")
    courted_princesses_ids: Mtm = Mtm("courted_princesses")


@dataclass
class Sword(Model):
    name: str
    length: int
    owner_id: Oto = Oto("knights")


@dataclass
class DeadDragon(Model):
    name: str
    age: int
    killer_id: Mto = Mto("knights")


@dataclass
class CourtedPrincess(Model):
    name: str
    age: int
    suitors_ids: Mtm = Mtm("knights")
```

## Oto (one-to-one)

Use `Oto("target_table")` on each side, usually with `*_id` field names.

```python
knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword_id": "s1"})
swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})

knight = knights.get(_id="k1")
sword = swords.get(_id="s1")

print(knight.obj.sword.obj.name)   # Excalibur
print(sword.obj.owner.obj.name)    # Arthur
```

Reverse assignment is also resolved:

```python
knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
swords.insert({"_id": "s2", "name": "Durandal", "length": 110, "owner_id": "k2"})

print(knights.get(_id="k2").obj.sword.obj.name)  # Durandal
```

Updating an Oto link keeps uniqueness by clearing the previous owner side.

## Mto (many-to-one)

Use `Mto("target_table")` on the child side.

```python
knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})

dragon = dragons.get(_id="d1")
print(dragon.obj.killer.obj.name)  # Arthur
```

## Otm (one-to-many)

Use `Otm("target_table")` on the parent side to expose reverse collections.

```python
knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
dragons.insert({"_id": "d2", "name": "Fafnir", "age": 150, "killer_id": "k1"})

arthur = knights.get(_id="k1")
print([d.obj.name for d in arthur.obj.dragons_killed])  # ["Smaug", "Fafnir"]
```

Important: `Otm` is computed from the opposite `Mto` side.
Passing `dragons_killed_ids` in insert/update payloads is ignored.

## Mtm (many-to-many)

Use `Mtm("target_table")` on both sides.
Silly ORM manages a join table automatically.

```python
princesses.insert({"_id": "p1", "name": "Guenievre", "age": 22})
princesses.insert({"_id": "p2", "name": "Elaine", "age": 20})

knights.insert({
    "_id": "k1",
    "name": "Arthur",
    "age": 40,
    "courted_princesses_ids": ["p1", "p2"],
})

arthur = knights.get(_id="k1")
print([p.obj.name for p in arthur.obj.courted_princesses])

guenievre = princesses.get(_id="p1")
print([k.obj.name for k in guenievre.obj.suitors])
```

Update replaces links:

```python
knights.update("k1", courted_princesses=["p2"])
```

Duplicates are ignored and invalid MTM payload types raise `SillyDbError`.

## Relational filters

Relational fields can be used in `filter()` with the same operators as scalar fields.

```python
# Oto
knights.filter(sword__name="Excalibur").all()

# Mto
dragons.filter(killer__name="Lancelot").all()

# Otm (reverse)
knights.filter(dragons_killed__name="Smaug").all()

# Mtm + operator
knights.filter(courted_princesses__age__gt=18).all()
```

## Notes

- Navigate resolved relations via `.obj` on returned `QItem` values.
- Scalar-style FK fields are typically named with `_id` suffix (`sword_id`, `killer_id`, `owner_id`).
- Mtm join table and relation indexes are created automatically.
