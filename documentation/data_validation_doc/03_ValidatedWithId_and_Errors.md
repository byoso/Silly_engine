[data_validation index](00_data_validation_index.md)

# ValidatedWithId and errors

ValidatedWithId extends ValidatedDataClass by adding an _id field with automatic uuid4 generation.

## Storage-friendly model

```python
from dataclasses import dataclass
from silly_engine.data_validation import ValidatedWithId

@dataclass
class Character(ValidatedWithId):
    name: str = ""
    age: int = 0

item = Character(name="Merlin", age=99)
print(item._id)
```

## Error handling

Use DataValidationError to catch type and business-rule failures.

```python
from silly_engine.data_validation import DataValidationError

try:
    Character(name="Merlin", age="old")
except DataValidationError as err:
    print(f"validation failed: {err}")
```

## Notes

- _id is generated automatically when not provided
- custom _validate() rules still run in subclasses
