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

print(knight.q.sword.get().q.name)   # Excalibur
print(sword.q.owner.get().q.name)    # Arthur
```

Reverse assignment is also resolved:

```python
knights.insert({"_id": "k2", "name": "Lancelot", "age": 35})
swords.insert({"_id": "s2", "name": "Durandal", "length": 110, "owner_id": "k2"})

print(knights.get(_id="k2").q.sword.get().q.name)  # Durandal
```

Updating an Oto link keeps uniqueness by clearing the previous owner side.

## Mto (many-to-one)

Use `Mto("target_table")` on the child side.

```python
knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})

dragon = dragons.get(_id="d1")
print(dragon.q.killer.get().q.name)  # Arthur
```

## Otm (one-to-many)

Use `Otm("target_table")` on the parent side to expose reverse collections.

```python
knights.insert({"_id": "k1", "name": "Arthur", "age": 40})
dragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killer_id": "k1"})
dragons.insert({"_id": "d2", "name": "Fafnir", "age": 150, "killer_id": "k1"})

arthur = knights.get(_id="k1")
print([d.q.name for d in arthur.q.dragons_killed.to_list()])  # ["Smaug", "Fafnir"]
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
print([p.q.name for p in arthur.q.courted_princesses.to_list()])

guenievre = princesses.get(_id="p1")
print([k.q.name for k in guenievre.q.suitors.to_list()])
```

Incremental mutation through relation accessors:

```python
arthur = knights.get(_id="k1")

arthur.q.sword.add("s1")
arthur.q.sword.remove()

arthur.q.dragons_killed.add("d1")
arthur.q.dragons_killed.remove("d1")

arthur.q.courted_princesses.add("p2")
arthur.q.courted_princesses.remove("p2")
```

For full replacement, `update(...)` still works:

```python
knights.update("k1", courted_princesses_ids=["p2"])
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

- Navigate resolved relations via `.q` on returned `QItem` values.
- Scalar-style FK fields are typically named with `_id` suffix (`sword_id`, `killer_id`, `owner_id`).
- Mtm join table and relation indexes are created automatically.


# About chaining queries

```
We could do:
swords.filter_first(_id="s1").q.owner.get().q.name

This query is composed like this:

swords : Table
.filter_first(_id="s1") -> QItem or None
.q -> Accessor
.owner -> QRef
.get() -> QItem or None
.q -> Accessor
.name -> value
```
But, knowing that when a QItem is return, it could also be None, this long query could raise an error.

So we should do instead:
```
sword = swords.filter_first(_id="s1")
knight = sword.q.owner.get() if sword is not None else None
knight_name = knight.q.name if knight is not None else None
```

## Better hover typing in VS Code (Protocol + cast)

Because relation attributes on `.q` are resolved dynamically, Pylance may show broad types.
You can define a Protocol and cast the accessor for better hover/completion.

```python
from typing import Protocol
from silly_engine.silly_orm import cast_accessor
from silly_engine.silly_orm.relation_views import QList, QRef


class KnightAccessor(Protocol):
    name: str
    sword: QRef
    dragons_killed: QList
    courted_princesses: QList


arthur = knights.filter_first(_id="k1")
if arthur is not None:
    q = cast_accessor(arthur.q, KnightAccessor)
    q.sword.add("s1")
    q.courted_princesses.add("p2")
```

This cast is typing-only and does not change runtime behavior.
