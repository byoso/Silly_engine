[text_tools index](00_text_tools_index.md)

# Colors

The Color class provides ANSI color constants for terminal output.

## Quick start

```python
from silly_engine.text_tools import c

print(f"{c.info}info message{c.end}")
print(f"{c.warning}warning message{c.end}")
print(f"{c.success}success message{c.end}")
```

## Notes

- c is a ready-to-use Color instance
- Color.demo() prints all available color attributes
- aliases include info, warning, success, danger
