[logger index](00_logger_index.md)

# logger introduction

The logger module provides a preconfigured Logger class with colored output for common logging levels.
It also exposes a reusable CustomFormatter and a helper to build log prefixes.

## Quick start

```python
from silly_engine.logger import Logger

logger = Logger("my-app")
logger.set_level("DEBUG")

logger.debug("debug message")
logger.info("ready")
logger.warning("careful")
logger.error("something failed")
```

## Constructor options

Logger accepts these options:

- name: logger name
- level: DEBUG, INFO, WARNING, ERROR, or CRITICAL
- display_date: include timestamp in prefix
- display_name: include logger name in prefix
- display_level: include level name in prefix
- prefix_format: fully custom prefix format string (overrides display_* flags)

Example:

```python
from silly_engine.logger import Logger

logger = Logger(
	name="my-app",
	level="INFO",
	display_date=False,
	display_name=True,
	display_level=True,
)
```

## Choosing level at runtime

```python
logger.set_level("WARNING")
```

## Notes

- Logger extends logging.Logger
- A stream handler is attached automatically
- set_level() expects one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
- setLevel() still exists through logging.Logger inheritance, but set_level() is the module helper API
