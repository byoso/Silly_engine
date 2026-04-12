[router index](00_router_index.md)

# router introduction

router provides route-based command dispatch for CLI apps, as an alternative to flag-heavy parsing.

## Quick start

```python
from silly_engine.router import Router, RouterError

router = Router(name="dev router")
router.add_routes([
    [["", "-h", "--help"], router.display_help, "show this help"],
    ["ping", lambda: print("pong"), "health check"],
])

try:
    router.query(["ping"])
except RouterError as err:
    print(err)
```

## Notes

- route definitions are [path, callback, description]
- plain strings in add_routes() are accepted as help section labels
