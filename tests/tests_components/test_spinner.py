import pytest
from silly_engine.components.spinner import run_with_spinner


def test_run_with_spinner_returns_result():
    result = run_with_spinner(lambda: 42)
    assert result == 42


def test_run_with_spinner_passes_args():
    def add(a, b):
        return a + b

    result = run_with_spinner(add, 3, 5)
    assert result == 8


def test_run_with_spinner_passes_kwargs():
    def greet(name="world"):
        return f"hello {name}"

    result = run_with_spinner(greet, name="spinner")
    assert result == "hello spinner"


def test_run_with_spinner_propagates_exception():
    def boom():
        raise ValueError("oops")

    with pytest.raises(ValueError, match="oops"):
        run_with_spinner(boom)
