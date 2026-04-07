from dataclasses import dataclass

import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.models import Model
from silly_engine.silly_orm.relations import Mtm, Otm, Oto, Mto


@dataclass
class Knight(Model):
    name: str
    age: int
    sword_id: Oto | None = Oto("swords")
    dragons_killed_ids: Otm | None = Otm("dead_dragons")
    courted_princesses_ids: Mtm | None = Mtm("courted_princesses")


@dataclass
class Sword(Model):
    name: str
    length: int
    owner_id: Oto | None = Oto("knights")


@dataclass
class DeadDragon(Model):
    name: str
    age: int
    killer_id: Mto | None = Mto("knights")


@dataclass
class CourtedPrincess(Model):
    name: str
    age: int
    suitors_ids: Mtm | None = Mtm("knights")


@pytest.fixture
def orm_tables():
    db = SillyDb(":memory:")
    knights = db.table("knights", Knight)
    swords = db.table("swords", Sword)
    dragons = db.table("dead_dragons", DeadDragon)
    princesses = db.table("courted_princesses", CourtedPrincess)
    try:
        yield db, knights, swords, dragons, princesses
    finally:
        db.close()
