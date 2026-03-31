#! /usr/bin/env python3

from silly_engine import DataValidationError, ValidatedDataClass, ValidatedWithId
from dataclasses import dataclass, field
from typing import List, Dict

"""Simple test cases and examples for ValidatedDataClass"""

@dataclass(init=False)
class Truc(ValidatedDataClass):
    foo: str = ""
    bar: int = 0
    enable: bool = False
    a_list: List[int] = field(default_factory=list)
    data: Dict[str, int] = field(default_factory=dict)

    def _validate(self) -> None:
        if len(self.a_list) > 3:
            raise DataValidationError("Liste must not exceed 2 elements")


# nominal case
data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": 0, "a_list": [1, 2, 3], "data": {"a": 1, "b": 2}}
truc = Truc(**data)
print("- Nominal case -> truc: \n", truc)

# error case typing
try:
    data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": True, "a_list": [1, 2, 3], "data": {0: 1, "b": 2}}
    truc = Truc(**data)
except DataValidationError as e:
    print("- Error case typing -> truc:")
    print(f"Validation error: {e}")

# error case _validate
try:
    data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": True, "a_list": [1, 2, 3, 4], "data": {"a": 1, "b": 2}}
    truc = Truc(**data)
except DataValidationError as e:
    print("- Error case _validate -> truc:")
    print(f"Validation error: {e}")

# default case
truc = Truc(**{})
print("- Default case -> truc: \n", truc)

@dataclass
class Machin(ValidatedWithId):
    name: str = ""
    age: int = 0

machin = Machin(name="machin", age=30)

print("- Machin with id -> machin: \n", machin)