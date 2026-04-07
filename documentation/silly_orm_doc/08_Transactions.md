[silly_orm index](00_silly_orm_index.md)

# Transactions

Use `db.transaction()` for atomic blocks.

```python
from silly_orm.tools import SillyDbError


try:
    with db.transaction():
        Knights.insert({"name": "Arthur", "age": 40})
        Knights.insert({"_id": "k1", "name": "Duplicate", "age": 20})
except SillyDbError:
    # Whole block is rolled back
    pass
```

## Notes

- Transactions are atomic: all changes are committed or all rolled back.
- Nested transactions are supported safely.
- `db.rollback()` is also available for manual rollback cases.
