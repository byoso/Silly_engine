#! /usr/bin/env python3

from dataclasses import dataclass
import random
from typing import Any

from silly_engine import (
    SillyDb,
    ValidatedWithId,
    Oto,
    rename_field,
    remove_field
)

db = SillyDb("migrations_test.sqlite3")

# migration test
# Adding a model:
@dataclass
class Castle(ValidatedWithId):
    name: str = ""
    location: str = ""
    color: str = ""
    archers: int = 0
    # defenders: int = 0
    owner_id: Oto | Any = Oto(target="knights")  # same type as the relation's target _id (here str)

Castles = db.table("manors", Castle)

def create_random_castle(nbre: int = 1) -> None:
    names = ["Camelot", "Tintagel", "Joyous Gard", "Castle of the Lake", "Castle of the Forest"]
    locations = ["England", "Scotland", "Wales", "Ireland", "France"]
    colors = ["Red", "Blue", "Green", "Yellow", "Black"]
    for i in range(nbre):
        castle = Castle(
            name=random.choice(names),
            location=random.choice(locations),
            color=random.choice(colors),
            archers=random.randint(10, 100),
        )
        Castles.save(castle)

# comment/uncomment to test the migration feature
# create_random_castle(10)

from silly_engine.silly_db import rename_table, rename_field, remove_field

def mig_1_0_0(db: SillyDb) -> None:
    """Example migration function to add a new table for castles."""
    rename_field(db, "castles", "archers", "defenders")

def mig_1_1_0(db: SillyDb) -> None:
    """Example migration function to rename a field in the castles table."""
    remove_field(db, "castles", "color")

def mig_1_2_0(db: SillyDb) -> None:
    """Example migration function to rename a field in the castles table."""
    rename_table(db, "castles", "manors")

db.migrate([
    # ("1.0.0", mig_1_0_0),
    # ("1.1.0", mig_1_1_0),
    ("1.2.0", mig_1_2_0),
    ])