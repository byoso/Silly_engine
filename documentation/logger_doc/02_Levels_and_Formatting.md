[logger index](00_logger_index.md)

# Levels and formatting

The module maps string levels to logging constants and formats each level with ANSI colors.

## Format shape

Each line uses this pattern:

- [timestamp][logger-name][level] message

## Available level names

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

## Caveats

- setLevel() takes uppercase keys from the internal map
- this logger is terminal-oriented because it uses ANSI colors
