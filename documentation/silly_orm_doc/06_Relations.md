[silly_orm index](00_silly_orm_index.md)

# Relations

Built-in relation types:

- `Oto`: one-to-one
- `Mto`: many-to-one
- `Otm`: one-to-many
- `Mtm`: many-to-many

```python
from dataclasses import dataclass
from silly_orm.models import Model
from silly_orm.relations.oto import Oto


@dataclass
class Knight(Model):
    name: str
    sword: Oto = Oto("swords")


@dataclass
class Sword(Model):
    name: str
    owner: Oto = Oto("knights")
```

```python
Swords.insert({"_id": "s1", "name": "Excalibur"})
Knights.insert({"name": "Arthur", "sword": "s1"})

arthur = Knights.filter(name="Arthur").first()
print(arthur.obj.sword.obj.name)
```

## Notes

- Relation navigation is available through `.obj` accessors.
- Relational filtering is supported (example: `sword__name="Excalibur"`).
