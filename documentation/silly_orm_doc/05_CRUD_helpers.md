[silly_orm index](00_silly_orm_index.md)

# CRUD helpers

Silly ORM exposes simple helpers for common operations.

## Create (Insert)

```python
# Basic insert
Knights.insert({"name": "Arthur", "age": 40})

# Insert with explicit ID
Knights.insert({"_id": "k1", "name": "Arthur", "age": 40})

# Insert returns nothing; fetch with get() or filter()
```

## Read (Get, Filter, Query)

### Simple fetch

```python
# Get single record by condition (returns item or None)
arthur = Knights.get(name="Arthur")
```

### Query with filters

```python
# All young knights
young = Knights.filter(age__lt=35).all()

# Or iterate directly (no .all() needed)
for knight in Knights.filter(age__lt=35):
    print(knight.obj.name)

# Or convert to list
young = list(Knights.filter(age__lt=35))
```

### Filter operators

```python
# Operators: __eq (default), __gt, __lt, __gte, __lte, __in, __contains
Knights.filter(age__gt=30)              # age > 30
Knights.filter(age__gte=30)             # age >= 30
Knights.filter(age__lt=50)              # age < 50
Knights.filter(age__lte=50)             # age <= 50
Knights.filter(name__contains="rth")    # LIKE '%rth%'
Knights.filter(age__in=[25, 35])        # IN (25, 35)
```

### Chain query methods

```python
# filter() returns Query object, so you can chain
Knights.filter(age__gt=30).order_by("age").limit(5).all()

# .first() returns single item (or None)
oldest = Knights.filter(age__gt=30).order_by("-age").first()

# .count() returns total matching items (as int)
count = Knights.filter(age__gt=30).count()

# order_by() accepts field name (asc) or "-field" (desc)
Knights.filter(age__gt=30).order_by("-age")  # descending
```

### Relational filters

```python
# Filter by relation-linked field
knights_with_excalibur = Knights.filter(sword__name="Excalibur")
smaug_slayer = Dragons.filter(killer__name="Lancelot")
```

## Update

```python
# Update by ID
knights_table.update(arthur.obj._id, age=41)

# Pass multiple fields
Knights.update(arthur.obj._id, age=41, name="King Arthur")

# Bulk update with filter chain
affected = Knights.update(name="Veteran").filter(age__gte=35).execute()
# Short alias
affected = Knights.update(name="Veteran").filter(age__gte=35).apply()
print(affected)  # number of updated rows
```

## Delete

```python
# Delete by ID
Knights.delete_by_id(arthur.obj._id)

# Or pass QItem directly
Knights.delete(arthur)  # uses arthur._data["_id"]

# Or pass the ID
Knights.delete("custom_id")

# Bulk delete with filter chain
affected = Knights.delete().filter(age__lt=30).execute()
# Short alias
affected = Knights.delete().filter(age__lt=30).apply()
print(affected)  # number of deleted rows
```

## Pagination

```python
# Paginate results
page = Knights.filter(age__gt=30).paginate(page_size=10, page=1)

# Access results and metadata
for knight in page.data:      # page.data contains QItems
    print(knight.obj.name)

print(page.page)              # Current page (1-indexed)
print(page.page_size)         # Items per page
print(page.total)             # Total matching records

# Get next page
page2 = Knights.filter(age__gt=30).paginate(page_size=10, page=2)
```

## Count

```python
# Count all records in table
total = Knights.count()

# Count with filters
young_count = Knights.count(age__lt=35)
old_count = Knights.filter(age__gte=35).count()

# Chainable on queries
big_count = Knights.filter(age__gt=30).order_by("age").count()
```

## Convert to dict or JSON

### QItem conversion

```python
# Single item to dict
arthur_dict = arthur.dict()      # {"_id": "k1", "name": "Arthur", "age": 40}

# Single item to JSON string
arthur_json = arthur.json()      # '{"_id": "k1", "name": "Arthur", "age": 40}'
```

### Query result conversion

```python
# Get all results as list of dicts (not QItems)
dicts = Knights.filter(age__gt=30).dict()

# Get all results as JSON string
json_str = Knights.filter(age__gt=30).json()
```

### Pagination conversion

```python
# Pagination result to dict
page_dict = page.dict()
# Returns: {"data": [...], "page": 1, "page_size": 10, "total": 42}

# Pagination result to JSON
page_json = page.json()
```

## Notes

- `filter()` always returns a `Query` object; use `.all()`, `.first()`, or iterate for results.
- `Query` objects are iterable via `__iter__()` and implement lazy evaluation at iteration time.
- Chainable bulk mutations use `.execute()` as terminal operation.
- `.apply()` is a short alias for `.execute()`.
    Example: `Knights.update(name="Veteran").filter(age__gte=35).apply()`.
- Without explicit transaction block, write helpers auto-commit and rollback on errors.
- Relational filters work across all relation types: `Oto`, `Mto`, `Otm`, `Mtm`.
