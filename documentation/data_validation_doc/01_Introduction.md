[data_validation index](00_data_validation_index.md)

# data_validation introduction

The data_validation module provides dataclass-based validation with typed fields, generic collection checks, and optional custom domain validation.

## Quick start

```python
from dataclasses import dataclass, field
from typing import List, Dict

from silly_engine.data_validation import ValidatedDataClass, DataValidationError

@dataclass(init=False)
class Profile(ValidatedDataClass):
    name: str = ""
    age: int = 0
    tags: List[str] = field(default_factory=list)
    meta: Dict[str, int] = field(default_factory=dict)

    def _validate(self) -> None:
        if self.age < 0:
            raise DataValidationError("age must be >= 0")

user = Profile(name="Alice", age=28, tags=["admin"], meta={"score": 12})
print(user)
```

## What it validates

- simple types: int, str, float, bool
- typed collections: List[T], Dict[K, V]
- optional custom rules in _validate()

## Related pages

- [02 ValidatedDataClass](02_ValidatedDataClass.md)
- [03 ValidatedWithId and Errors](03_ValidatedWithId_and_Errors.md)
