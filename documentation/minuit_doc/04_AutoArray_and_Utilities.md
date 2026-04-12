[minuit index](00_minuit_index.md)

# AutoArray and utilities

AutoArray renders list-of-dict data in a table-like string with optional alternating colors.

## Example

```python
from silly_engine.minuit import AutoArray
from silly_engine.text_tools import c

rows = [
    {"name": "Conan", "strength": 90, "mana": None},
    {"name": "Merlin", "strength": 5, "mana": 10},
]

arr = AutoArray(
    rows,
    title="Characters",
    include=["name", "strength", "mana"],
    color_1=c.bg_cyan,
    color_2=c.bg_blue,
)
print(arr)
```

## Utilities

- TextField / print_formated for wrapped messages
- Confirmation for yes/no prompts with defaults
- clear() for cross-platform terminal cleaning
