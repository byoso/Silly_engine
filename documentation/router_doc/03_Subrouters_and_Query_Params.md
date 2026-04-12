[router index](00_router_index.md)

# Subrouters and query params

Router supports nested routers via Subrouter and query-string style parameters at the end of a command.

## Query params

A query suffix starts with ? and joins params with +.

```text
query ?foo=bar+debug=1
```

Your callback can receive query_params in kwargs.

## Subrouter example

```python
from silly_engine.router import Router, Subrouter

admin = Router(name="admin")
admin.add_route(["stats", lambda: "stats", "admin stats"])

root = Router(name="root")
root.add_route(Subrouter("admin", admin, "admin commands"))

print(root.query(["admin", "stats"]))
```

## Notes

- query parameters must appear once and at the end
- unknown routes raise RouterError with status 404
