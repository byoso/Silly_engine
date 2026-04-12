[silly_orm index](00_silly_orm_index.md)

# Project structure (quick guide)

## Recommended option (clean and scalable)

You can find a boilerplate in silly_orm/project_structure

```text
project/
	silly_orm/                 # local package copy (not pip-installed)
	app/
		db/
			__init__.py
			connection.py          # db = SillyDb(...)
			models/
				__init__.py
				knight.py
				sword.py
				dead_dragon.py
				courted_princess.py
			registry.py            # table declarations (Knights = db.table(...))
			migrations/
				__init__.py
				0001_init.py         # def mig_1_0_0(db): ...
				0002_add_x.py
			migrate.py             # loads and runs pending migrations
		services/
			...
	main.py
```

## small project structure

```text
project/
	app/
		db/
			connection.py      # db = SillyDb("...")
			models/            # dataclass models only
			migrations/        # migration files (0001_*.py, 0002_*.py, ...)
			migrate.py         # runs pending migrations
			registry.py        # table declarations (db.table(...))
	main.py
```

## Startup order

Always boot in this order:

1. Create the DB connection.
2. Run migrations.
3. Declare ORM tables.
4. Run app logic.

This avoids schema/model mismatch.

## Migration function signature

Migration functions should accept `db`:

```python
def mig_1_0_0(db):
		db.execute("ALTER TABLE ...")
```

And register them like this:

```python
db.migrate([
		("1.0.0", mig_1_0_0),
		("1.1.0", mig_1_1_0),
])
```

## Keep it simple

- Models file: only model classes.
- Migrations file: only migration functions.
- Registry file: only `db.table(...)` declarations.
- `main.py`: call migrate first, then import/use tables.


## main.py example

You usually import both:

- the migration runner
- the table registry (which already uses the shared `db`)

```python
# main.py
from app.db.migrate import run_migrations
from app.db.registry import db, Knights


def main() -> None:
	run_migrations(db)

	# ORM usage
	Knights.insert({"name": "Arthur", "age": 40})
	print([k.q.name for k in Knights.filter().all()])


if __name__ == "__main__":
	main()
```

If your migrations are executed before app startup (CLI/deploy step),
you can import only `db` and your tables in `main.py`.
