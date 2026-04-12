[router index](00_router_index.md)

# Route patterns and types

Route paths support parameter placeholders like <name:type>.

## Typed parameters

```python
from silly_engine.router import Router

router = Router()
router.add_route(["add <x:int>", lambda x: x * 2, "double an integer"])
router.add_route(["scale <v:float>", lambda v: v * 1.5, "scale float"])

print(router.query(["add", "3"]))
print(router.query(["scale", "2.0"]))
```

## Supported converters

- int
- float
- bool (expects 0 or 1 style values)
- str (default when no explicit type is provided)

## Errors

Type mismatch raises RouterError with status 400.
