[data_validation index](00_data_validation_index.md)

# ValidatedDataClass

ValidatedDataClass is the base class used to enforce field types and apply custom validation logic.

## Typical model pattern

```python
from dataclasses import dataclass, field
from typing import List

from silly_engine.data_validation import ValidatedDataClass, DataValidationError

@dataclass(init=False)
class Task(ValidatedDataClass):
    title: str = ""
    done: bool = False
    points: List[int] = field(default_factory=list)

    def _validate(self) -> None:
        if len(self.points) > 3:
            raise DataValidationError("points must contain at most 3 values")
```

## Construction notes

- You can call Task(**data)
- A single positional dict is also supported for legacy style
- Unknown extra keys are ignored unless they are copied by your custom logic

## Type conversion behavior

- bool fields accept bool values
- bool also accepts int values (0 or 1 are cast to False or True)
- invalid types raise DataValidationError

## Related pages

- [01 Introduction](01_Introduction.md)
- [03 ValidatedWithId and Errors](03_ValidatedWithId_and_Errors.md)
