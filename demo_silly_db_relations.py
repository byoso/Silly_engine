#! /usr/bin/env python3

"""
This is a demo of how to use the SillyDb with relations between tables.
It creates a simple database of knights, swords, dead dragons and courted princesses,
and demonstrates how to create, update and delete records with relations.

Note that the relations are defined using the Oto, Mto, Otm and Mtm classes,
from the silly_engine.silly_db.models module.

As this classes are used for input and output, the typing is always
<RelationshipClass> | Any, the model is checked anyway.

Check the code to see how to type.

"""

from dataclasses import dataclass
from typing import Any
import random

from silly_engine import (
    SillyDb,
    SillyDbError,
    DataValidationError,
    ValidatedWithId,
    Oto, Mto, Otm, Mtm,
    Table
    )

EXEC_ALL = True


@dataclass
class Knight(ValidatedWithId):
    name: str = ""
    age: int = 0
    sword_id: Oto | Any = Oto(target="swords")  # same type as the relation's target _id (here str)
    dragons_killed_ids: Otm | Any = Otm(target="dead_dragons")  # same type as the relation's target _id (here str)
    courted_princesses_ids: Mtm | Any = Mtm(target="courted_princesses")  # same type as the relation's target _id (here str)
    castle_id: Oto | Any = Oto(target="castles")  # same type as the relation's target _id (here str)

    def _validate(self) -> None:
        if self.age < 0:
            raise DataValidationError("Age must be a non-negative integer")


@dataclass
class Sword(ValidatedWithId):
    name: str = ""
    length: int = 0
    description: str = ""
    owner_id: Oto | Any = Oto(target="knights")  # same type as the relation's target _id (here str)

    def _validate(self) -> None:
        if self.length <= 0:
            raise DataValidationError("Length must be a positive integer")

@dataclass
class DeadDragon(ValidatedWithId):
    name: str = ""
    age: int = 0
    killed_by_id: Mto | Any = Mto(target="knights")  # same type as the relation's target _id (here str)

@dataclass
class CourtedPrincess(ValidatedWithId):
    name: str = ""
    age: int = 0
    suitors_ids: Mtm | Any = Mtm(target="knights")  # same type as the relation's target _id (here str)

db = SillyDb("demoRelations.sqlite3")
# recursive level is better set to 0 (default), you can play with it but it is not recommended


db.delete_all_tables()  # for testing purposes, to ensure a clean slate. Use with caution!

Knights: Table[Knight] = db.table("knights", Knight)
Swords: Table[Sword] = db.table("swords", Sword)
DeadDragons: Table[DeadDragon] = db.table("dead_dragons", DeadDragon)
CourtedPrincesses: Table[CourtedPrincess] = db.table("courted_princesses", CourtedPrincess)


def create_random_knight(nbre: int = 1) -> None:
    names = ["Arthur", "Lancelot", "Gawain", "Galahad", "Tristan"]
    salt = ["the Brave", "the Bold", "the Swift", "the Wise", "the Strong"]
    for i in range(nbre):
        knight = Knight(
            name=random.choice(names) + " " + random.choice(salt),
            age=random.randint(18, 60),
        )
        Knights.save(knight)

def create_random_sword(nbre: int = 1) -> None:
    names = ["Excalibur", "Durandal", "Joyeuse", "Tizona", "Zulfiqar"]
    salt = ["of Power", "of Destiny", "of the Ancients", "of the Dragon", "of the Phoenix"]
    for i in range(nbre):
        sword = Sword(
            name=random.choice(names) + " " + random.choice(salt),
            length=random.randint(50, 150),
        )
        Swords.save(sword)

def create_random_dead_dragon(nbre: int = 1) -> None:
    names = ["Smaug", "Fafnir", "Glaurung", "Ancalagon", "Tiamat"]
    salt = ["the Terrible", "the Mighty", "the Ancient", "the Cursed", "the Firebreather"]
    for i in range(nbre):
        dragon = DeadDragon(
            name=random.choice(names) + " " + random.choice(salt),
            age=random.randint(100, 1000),
        )
        DeadDragons.save(dragon)

def create_random_courted_princess(nbre: int = 1) -> None:
    names = ["Guinevere", "Isolde", "Elaine", "Nimue", "Rhiannon"]
    salt = ["of Camelot", "of the Lake", "of the Forest", "of the Mountain", "of the Sea"]
    for i in range(nbre):
        princess = CourtedPrincess(
            name=random.choice(names) + " " + random.choice(salt),
            age=random.randint(16, 30),
        )
        CourtedPrincesses.save(princess)

create_random_knight(10)
create_random_sword(10)

if not EXEC_ALL:
    input("Press Enter to continue...")

one_knight: Knight | None = Knights.get_first()  # avoid infinite recursion when printing
one_sword: Sword | None = Swords.get_first()
assert one_knight is not None and one_sword is not None, \
"There should be at least one knight and one sword in the database"

print("\nInitial state:")
print("One knight:", one_knight)
print("One sword:", one_sword)

one_knight.sword_id = one_sword
Knights.save(one_knight)

print("\nAfter Update:")
print("One knight:", Knights.get_by_id(one_knight._id, recursive_level=0))
assert one_knight.sword_id is not None, "One knight should have a sword after the update"
print("One sword:", Swords.get_by_id(one_sword._id))
if not EXEC_ALL:
    input("Press Enter to continue...")

second_sword: Sword = Swords.get_all()[1]
second_sword.owner_id = one_knight
Swords.save(second_sword)

print("\nAfter Update 2:")
print("One knight:", Knights.get_by_id(one_knight._id))
print("One sword:", Swords.get_by_id(one_sword._id))  # avoid infinite recursion when printing
print("Second sword:", Swords.get_by_id(second_sword._id))
if not EXEC_ALL:
    input("Press Enter to continue...")


one_knight.sword_id = None
Knights.save(one_knight)
print("\nAfter Update 3:")
print("One knight:", Knights.get_by_id(one_knight._id))
if not EXEC_ALL:
    input("Press Enter to continue...")

Swords.delete_one(second_sword)
print("\nAfter Deleting second sword:")
print("One knight:", Knights.get_by_id(one_knight._id))
print("One sword:", Swords.get_by_id(one_sword._id))
print("Second sword:", Swords.get_by_id(second_sword._id))

# Demo Mto Otm

create_random_dead_dragon(10)
one_dragon: DeadDragon | None = DeadDragons.get_first()
assert one_dragon is not None, "There should be at least one dead dragon in the database"
one_dragon.killed_by_id = one_knight
DeadDragons.save(one_dragon)
print("\nAfter setting killed_by for one dragon:")
print("One dragon:", DeadDragons.get_by_id(one_dragon._id))
assert one_dragon.killed_by_id is not None, "One dragon should have a killer after the update"
print("One knight:", Knights.get_by_id(one_knight._id))
assert one_knight.dragons_killed_ids is not None, "One knight should have a list of killed dragons after the update"


# demo Mtm
create_random_courted_princess(10)
all_princesses = CourtedPrincesses.get_all()
assert len(all_princesses) == 10, "There should be at least one courted princess in the database"
one_princess: CourtedPrincess = all_princesses[0]
assert one_princess is not None, "There should be at least one courted princess in the database"
one_princess.suitors_ids = [one_knight]
CourtedPrincesses.save(one_princess)
print("\nAfter setting suitors for one princess:")
print("One princess:", CourtedPrincesses.get_by_id(one_princess._id))
assert one_princess.suitors_ids is not None, "One princess should have a list of suitors after the update"
print("One knight:", Knights.get_by_id(one_knight._id))
assert one_knight.courted_princesses_ids is not None, "One knight should have a list of courted princesses after the update"

print(f"\nDatabase tables: {db.tables.keys()}\n")

# update one knight to court a second princess
princess_2 = all_princesses[1]
princess_3 = all_princesses[2]
one_knight.courted_princesses_ids.append(princess_2._id)
one_knight.courted_princesses_ids.append(princess_3._id)
Knights.save(one_knight)
print("\nAfter adding a second princess to one knight's courted princesses:")
print("One knight:", Knights.get_by_id(one_knight._id))
print("Princess 2:", CourtedPrincesses.get_by_id(princess_2._id))

# remove a princess and update
# one_knight = Knights.get_by_id(one_knight._id)  # refresh from db to avoid issues with the list reference
one_knight.courted_princesses_ids.remove(princess_2._id)
Knights.save(one_knight)
print("\nAfter removing princess 2 from one knight's courted princesses:")
print("One knight:", Knights.get_by_id(one_knight._id))
print("Princess 2:", CourtedPrincesses.get_by_id(princess_2._id))
