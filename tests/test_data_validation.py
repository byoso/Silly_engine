from dataclasses import dataclass
import pytest

from silly_engine.core.data_validation import _check_generic, ValidatedDataClass, DataValidationError
from typing import List, Dict, Any


def test_check_generic_simple_types():
    assert _check_generic(5, int) == 5
    assert _check_generic(True, bool) is True


def test_check_generic_list_and_dict():
    v = _check_generic(['a', 'b'], List[str])
    assert v == ['a', 'b']
    d = _check_generic({'k': 1}, Dict[str, int])
    assert d == {'k': 1}


def test_check_generic_type_error():
    with pytest.raises(DataValidationError):
        _check_generic('x', int, 'f')


def test_validated_dataclass_sets_fields_and_id():
    @dataclass
    class Simple(ValidatedDataClass):
        name: str = ""
        age: int = 0

    s = Simple({'name': 'bob', 'age': 30, '_id': 'xyz'})
    assert s.name == 'bob'
    assert s.age == 30
    assert s._id == 'xyz'
