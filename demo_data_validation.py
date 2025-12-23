#! /usr/bin/env python3

from silly_engine import DataValidationError, ValidatedDataClass
from dataclasses import dataclass, field

"""Simple test cases and examples for ValidatedDataClass"""

@dataclass
class Truc(ValidatedDataClass):
    foo: str = ""
    bar: int = 0
    enable: bool = False
    a_list: list[int] = field(default_factory=list)
    data: dict[str, int] = field(default_factory=dict)

    def _validate(self) -> None:
        if len(self.a_list) > 3:
            raise DataValidationError("Liste must not exceed 2 elements")


# nominal case
data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": 0, "a_list": [1, 2, 3], "data": {"a": 1, "b": 2}}
truc = Truc(data)
print(truc)

# error case typing
try:
    data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": True, "a_list": [1, 2, 3], "data": {0: 1, "b": 2}}
    truc = Truc(data)
    print(truc)
except DataValidationError as e:
    print(f"Validation error: {e}")

# error case _validate
try:
    data = {"foo": "toto", "bar": 12, "truc": "un truc", "enable": True, "a_list": [1, 2, 3, 4], "data": {"a": 1, "b": 2}}
    truc = Truc(data)
    print(truc)
except DataValidationError as e:
    print(f"Validation error: {e}")

# default case
truc = Truc({})
print(truc)