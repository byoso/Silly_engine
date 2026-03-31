from abc import ABC
from typing import Any

class SillyOrmRelation(ABC):
    pass

class Oto(SillyOrmRelation):
    """One To One relationship"""
    def __init__(self, target: str | Any) -> None:
        self.target = target

    def __str__(self) -> str:
        return f"Oto(target={self.target})"

class Mto(Oto):
    """Many To One relationship"""

    def __str__(self) -> str:
        return f"Mto(target={self.target})"

class Otm(SillyOrmRelation):
    """One To Many relationship"""
    def __init__(self, target: str | list[str]) -> None:
        # accept either a single target name or a list of target names
        if isinstance(target, list):
            self.targets = target
            # keep backward-compatible `target` as the first element
            self.target = target[0] if target else None
        else:
            self.target = target
            self.targets = [target]

    def __str__(self) -> str:
        return f"Otm(targets={self.targets})"


class Mtm(SillyOrmRelation):
    """Many To Many relationship (stored in a join table)

    Accepts a single target name or a list of target names (backward-compatible).
    """
    def __init__(self, target: str | list[str]) -> None:
        if isinstance(target, list):
            self.targets = target
            self.target = target[0] if target else None
        else:
            self.target = target
            self.targets = [target]

    def __str__(self) -> str:
        return f"Mtm(targets={self.targets})"

    def append(self, item: Any) -> None:
        """for static type checkers, to allow appending to the list of related IDs"""

    def remove(self, item: Any) -> None:
        """for static type checkers, to allow removing from the list of related IDs"""