[logger index](00_logger_index.md)

# logger introduction

The logger module provides a preconfigured Logger class with colored output for common logging levels.

## Quick start

```python
from silly_engine.logger import Logger

logger = Logger("my-app")
logger.setLevel("DEBUG")

logger.debug("debug message")
logger.info("ready")
logger.warning("careful")
logger.error("something failed")
```

## Notes

- Logger extends logging.Logger
- A stream handler is attached automatically
- setLevel() expects one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
