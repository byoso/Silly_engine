[logger index](00_logger_index.md)

# Levels and formatting

The module maps string levels to logging constants and formats each level with ANSI colors.

## API pieces involved in formatting

- get_prefix(date=True, name=True, level=True): builds the default prefix template
- CustomFormatter(...): applies level-based color output and message formatting
- Logger(...): creates a stream handler configured with CustomFormatter

## Format shape

Each line uses this pattern:

- [timestamp][logger-name][level] message

You can disable individual prefix sections with Logger display_date, display_name, and display_level.

## Custom prefix format

If prefix_format is passed to Logger or CustomFormatter, it is used as-is and takes priority over display_date/display_name/display_level.

Example:

```python
from silly_engine.logger import Logger

logger = Logger(
	"my-app",
	prefix_format="[%(name)s][custom] ",
)

# or (if prefix_format is None)

logger = Logger(
	"my-app",
    display_date = True,  # True is default
    display_name = True,
    display_level = True,
)


```

## Available level names

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

## Color mapping

- DEBUG: green
- INFO: blue
- WARNING: yellow
- ERROR: red
- CRITICAL: bold red

## Caveats

- set_level() takes uppercase keys from the internal map
- this logger is terminal-oriented because it uses ANSI colors
- fallback output for unknown levels is message-only
