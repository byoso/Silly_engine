[minuit index](00_minuit_index.md)

# Menu and navigation

Menu and MenuItem let you bind keys to callbacks and build simple terminal workflows.

## Example

```python
from silly_engine.minuit import Menu


def hello():
    print("hello")

menu = Menu([
    ("1", "say hello", hello),
    ("x", "exit", lambda: print("bye")),
], title="Main menu")

menu.ask()
```

## Notes

- invalid selection loops back to ask()
- clear_on_error can clear the terminal between retries
- MenuItem also works as a standalone callable wrapper
