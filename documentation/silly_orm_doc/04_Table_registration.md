[silly_orm index](00_silly_orm_index.md)

# Table registration

Register each model with `db.table(table_name, ModelClass)`.

```python
from silly_engine.silly_orm.db import SillyDb
from app.db.models import Knight


db = SillyDb("DB.sqlite3")
Knights = db.table("knights", Knight)
```

## Notes

- Register once at startup (usually in a registry module).
- Table creation and index setup are handled automatically.
- Run migrations before table registration in application boot flow.
