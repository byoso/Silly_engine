[text_tools index](00_text_tools_index.md)

# ASCII titles

Use Title and print_title to render large ASCII banners with optional color and letter overlap.

## Example

```python
from silly_engine.text_tools import Title, print_title, c

banner = Title("Silly Engine", color=c.green, step=2)
print(banner)

print_title("Demo", color=c.cyan)
```

## About the character map

The default mapping comes from components/ascii_map_01.py.

If you provide your own map, keep all letters aligned and keep a space character entry.
