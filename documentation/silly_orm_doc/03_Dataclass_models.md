[silly_orm index](00_silly_orm_index.md)

# Dataclass models

Use Python dataclasses that inherit from `Model`.

```python
from dataclasses import dataclass
from silly_engine.silly_orm.models import Model


@dataclass
class Knight(Model):
    name: str
    age: int
```

## Notes

- `_id` is generated automatically if not provided.
- Keep models focused on data shape and relation fields.

## Computed properties with `@property`

You can define computed properties on your model, and access them through the accessor (`item.q`).

```python
from dataclasses import dataclass
from silly_engine.silly_orm.models import Model


@dataclass
class Knight(Model):
    name: str
    age: int

    @property
    def label(self) -> str:
        return f"{self.name} ({self.age})"


arthur = Knights.filter_first(name="Arthur")
print(arthur.q.label)  # Arthur (40)
```

Behavior notes:

- Properties are read-only unless you explicitly define a setter.
- The value is computed each time you access `item.q.<property_name>`.
- Properties can rely on model fields present in the row data.

---

## The `Meta` inner class

Add an inner `Meta` class to configure the table's behavior. All attributes are optional.

```python
@dataclass
class Article(Model):
    title: str
    author: str
    status: str = "draft"

    class Meta(Model.Meta):
        table_name = "articles"
        ordering = ["-title"]
        defaults = {"status": "published"}
        unique = ["title"]
        indexes = ["author"]
        auto_now_add = True
        auto_now = True
        ttl = 3600
```

### Reference

| Attribute | Type | Description |
|---|---|---|
| `singleton` | `bool` | If `True`, only one row can exist in the table. Default: `False`. |
| `table_name` | `str` | Custom SQL table name. If omitted, defaults to the lowercase class name. |
| `ordering` | `list[str]` | Default ordering for queries. Prefix with `-` for descending (e.g. `["-created_at"]`). |
| `defaults` | `dict` | Field values applied automatically on insert if not provided in the payload. |
| `unique` | `list` | Unique constraints. Each entry is a field name (single) or a list of field names (composite). |
| `indexes` | `list[str]` | Fields to index with `CREATE INDEX`. |
| `auto_now_add` | `list[str]` | Set a unix timestamp column once on insert in the selected columns. |
| `auto_now` | `list[str]` | update a unix timestamp column on every update of the model in the selected columns. |
| `ttl` | `int` | Time-to-live in seconds. Adds a `_expires_at` column; expired records are filtered out automatically from all queries. |

### Details

#### `table_name`

Allows `db.table(MyModel)` to be called without an explicit name:

```python
@dataclass
class BlogPost(Model):
    title: str

    class Meta:
        table_name = "posts"

posts = db.table(BlogPost)  # uses "posts" as the SQL table name
```

Without `table_name`, `db.table(MyModel)` uses the lowercase class name (`blogpost`).

#### `ordering`

Applied automatically to every `filter()` call. Use `-` prefix for descending order.

```python
class Meta:
    ordering = ["-score"]  # highest score first
```

#### `defaults`

Values merged into the payload on insert, only for fields not already provided. The keys must match existing model fields.

```python
class Meta:
    defaults = {"status": "active"}
```

#### `unique`

Single-column constraint:
```python
class Meta:
    unique = ["email"]
```

Multi-column (composite) constraint:
```python
class Meta:
    unique = [["day", "hour"]]  # (day, hour) pair must be unique
```

Both can be combined:
```python
class Meta:
    unique = ["email", ["day", "hour"]]
```

#### `auto_now_add` and `auto_now`

```python
class Meta:
    auto_now_add = True  # _created_at set on insert
    auto_now = True      # _updated_at refreshed on every update
```

The values are stored as integer unix timestamps in `_created_at` and `_updated_at` columns, accessible via the raw `_data` dict on a `QItem`.

#### `ttl`

Records are not physically deleted automatically. Instead, an `_expires_at` column is set on insert (`now + ttl`) and expired rows are hidden from reads (`filter()`, `count()`, `get_by_id()`, `filter_first()`, etc.).

When you want to physically remove expired rows, call one of the explicit purge methods:

- `table.purge_ttl()` to purge one table (returns number of deleted rows)
- `db.purge_ttl()` to purge every registered TTL table (returns a dict `{table_name: deleted_count}`)

```python
class Meta:
    ttl = 60  # records expire after 60 seconds
```

```python
deleted = cache_table.purge_ttl()
print(deleted)  # 3

summary = db.purge_ttl()
print(summary)  # {'cache': 3, 'sessions': 1}
```

#### `singleton`

Enforces a single row via a `UNIQUE(_singleton_lock)` SQL constraint. Useful for settings or configuration tables.

```python
class Meta:
    singleton = True
```
