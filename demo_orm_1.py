#! /usr/bin/env python3

from dataclasses import dataclass
import random

from silly_engine.silly_orm.models import Model
from silly_engine.silly_orm.relations.oto import Oto
from silly_engine.silly_orm.relations.otm import Otm
from silly_engine.silly_orm.relations.mto import Mto
from silly_engine.silly_orm.relations.mtm import Mtm
from silly_engine.silly_orm.db import SillyDb



@dataclass
class Knight(Model):
    name: str
    age: int
    sword: Oto = Oto("swords")
    dragons_killed: Otm = Otm("dead_dragons")
    courted_princesses: Mtm = Mtm("courted_princesses")

@dataclass
class Sword(Model):
    name: str
    length: int
    owner: Oto = Oto("knights")

@dataclass
class DeadDragon(Model):
    name: str
    age: int
    killed_by: Mto = Mto("knights")

@dataclass
class CourtedPrincess(Model):
    name: str
    age: int
    suitors: Mtm = Mtm("knights")

    class Meta(Model.Meta):
        table_name = "courted_princesses"


db = SillyDb("DB.sqlite3")

Knights = db.table("knights", Knight)
Swords = db.table("swords", Sword)
DeadDragons = db.table("dead_dragons", DeadDragon)
CourtedPrincesses = db.table(CourtedPrincess)

def create_random_knight(n):
    for i in range(n):
        names = ["Arthur", "Lancelot", "Gawain", "Galahad", "Tristan"]
        nickname = ["the Brave", "the Bold", "the Swift", "the Wise", "the Just"]
        Knights.insert({
            "name": f"{random.choice(names)} {random.choice(nickname)}",
            "age": random.randint(20, 60),
        })

def create_random_sword(n):
    for i in range(n):
        names = ["Excalibur", "Durandal", "Joyeuse", "Tizona", "Zulfiqar"]
        nickname = ["of Power", "of the West", "of the Sun", "of the Moon", "of the Stars"]
        Swords.insert({
            "name": f"{random.choice(names)} {random.choice(nickname)}",
        "length": random.randint(30, 50),
    })

def create_random_dragon(n):
    for i in range(n):
        names = ["Smaug", "Fafnir", "Glaurung", "Ancalagon", "Tiamat"]
        nickname = ["the Terrible", "the Golden", "the Red", "the Black", "the Ancient"]
        DeadDragons.insert({
            "name": f"{random.choice(names)} {random.choice(nickname)}",
        "age": random.randint(100, 500),
    })

def create_random_princess(n):
    for i in range(n):
        names = ["Guinevere", "Isolde", "Elaine", "Nimue", "Rhiannon"]
        nickname = ["the Fair", "the Gentle", "the Wise", "the Enchanting", "the Radiant"]
        CourtedPrincesses.insert({
            "name": f"{random.choice(names)} {random.choice(nickname)}",
        "age": random.randint(18, 30),
    })

def create_sample_data(n=10):
    create_random_knight(n)
    create_random_sword(n)
    create_random_dragon(n)
    create_random_princess(n)


print("=== Create ===")

Knights.insert({"_id": "k1", "name": "Arthur", "age": 40, "sword": "s1", "courted_princesses": ["p1"]})
Knights.insert({"_id": "k2", "name": "Lancelot", "age": 35, "sword": "s2", "courted_princesses": ["p2"]})
Knights.insert({"_id": "k3", "name": "Gawain", "age": 31, "sword": "s3", "courted_princesses": ["p1", "p3"]})
Knights.insert({"_id": "k4", "name": "Galahad", "age": 28, "courted_princesses": ["p4"]})
Knights.insert({"_id": "k5", "name": "Percival", "age": 26})

Swords.insert({"_id": "s1", "name": "Excalibur", "length": 120})
Swords.insert({"_id": "s2", "name": "Durandal", "length": 110})
Swords.insert({"_id": "s3", "name": "Joyeuse", "length": 105})
Swords.insert({"_id": "s4", "name": "Tizona", "length": 115})

DeadDragons.insert({"_id": "d1", "name": "Smaug", "age": 300, "killed_by": "k1"})
DeadDragons.insert({"_id": "d2", "name": "Fafnir", "age": 150, "killed_by": "k2"})
DeadDragons.insert({"_id": "d3", "name": "Glaurung", "age": 220, "killed_by": "k1"})
DeadDragons.insert({"_id": "d4", "name": "Ancalagon", "age": 450, "killed_by": "k3"})

CourtedPrincesses.insert({"_id": "p1", "name": "Guenièvre", "age": 22})
CourtedPrincesses.insert({"_id": "p2", "name": "Elaine", "age": 20})
CourtedPrincesses.insert({"_id": "p3", "name": "Isolde", "age": 24})
CourtedPrincesses.insert({"_id": "p4", "name": "Nimue", "age": 19})
CourtedPrincesses.insert({"_id": "p5", "name": "Morgause", "age": 27})

print("created knights:", [item.q.name for item in Knights.filter().all()])
print("created swords:", [item.q.name for item in Swords.filter().all()])
print("created dragons:", [item.q.name for item in DeadDragons.filter().all()])
print("created princesses:", [item.q.name for item in CourtedPrincesses.filter().all()])

print("\n=== Read ===")

arthur = Knights.filter_first(_id="k1")
assert arthur is not None
young_knights = Knights.filter(age__lt=35).order_by("age").all()
lancelot = Knights.filter_first(name="Lancelot")
assert lancelot is not None

print("get(_id='k1') ->", arthur.q.name, arthur.q.age)
print("get(name='Lancelot') ->", lancelot.q.name, lancelot.q.age)
print("filter(age__lt=35) ->", [item.q.name for item in young_knights])

print("\n=== Update ===")

Knights.update("k4", sword="s4")
Knights.update("k2", age=36, courted_princesses=["p2", "p3"])
Knights.update("k5", courted_princesses=["p5"])

galahad = Knights.get_by_id("k4")
assert galahad is not None
lancelot = Knights.get_by_id("k2")
assert lancelot is not None
percival = Knights.get_by_id("k5")
assert percival is not None

print("updated Galahad sword ->", galahad.q.sword.q.name)
print("updated Lancelot age ->", lancelot.q.age)
print("updated Lancelot princesses ->", [p.q.name for p in lancelot.q.courted_princesses])
print("created without relation, then linked ->", percival.q.name, [p.q.name for p in percival.q.courted_princesses])

print("\n=== Delete ===")

print("before delete, Galahad princesses ->", [p.q.name for p in galahad.q.courted_princesses])
CourtedPrincesses.delete_by_id("p4")
galahad = Knights.filter_first(_id="k4")
assert galahad is not None

print("after delete, princess p4 exists ->", CourtedPrincesses.filter_first(_id="p4"))
print("after delete, Galahad princesses ->", [p.q.name for p in galahad.q.courted_princesses])

print("\n=== Relation Queries ===")

for k in Knights.filter(sword__name="Excalibur").all():
    print("Oto query:", k.q.name, "has sword", k.q.sword.q.name)

for k in Knights.filter(dragons_killed__name="Smaug").all():
    print("Otm query:", k.q.name, "killed dragon Smaug")

for d in DeadDragons.filter(killed_by__name="Lancelot").all():
    print("Mto query:", d.q.name, "was killed by", d.q.killed_by.q.name)

for k in Knights.filter(courted_princesses__age__gt=18).all():
    print("Mtm query:", k.q.name, "courted", [p.q.name for p in k.q.courted_princesses])

print("\n=== Object Navigation Examples ===")

gawain = Knights.filter_first(_id="k3")
assert gawain is not None
durandal = Swords.filter_first(_id="s2")
assert durandal is not None
smaug = DeadDragons.filter_first(_id="d1")
assert smaug is not None
isolde = CourtedPrincesses.filter_first(_id="p3")
assert isolde is not None

assert arthur is not None
print("Oto from Knight -> Sword:")
print(arthur.q.name, "uses", arthur.q.sword.q.name)

print("Oto from Sword -> Knight:")
if durandal is not None and durandal.q.owner is not None:
    print(durandal.q.name, "belongs to", durandal.q.owner.q.name)

print("Otm from Knight -> DeadDragons:")
print(gawain.q.name, "killed", [dragon.q.name for dragon in gawain.q.dragons_killed])

print("Mto from DeadDragon -> Knight:")
print(smaug.q.name, "was killed by", smaug.q.killed_by.q.name)

print("Mtm from Knight -> CourtedPrincesses:")
print(gawain.q.name, "courted", [princess.q.name for princess in gawain.q.courted_princesses])

print("Mtm from CourtedPrincess -> Knights:")
print(isolde.q.name, "has suitors", [knight.q.name for knight in isolde.q.suitors])

print("\nMutable relation helpers (add/remove):")
gawain.q.add("courted_princesses", isolde)
print("after add,", gawain.q.name, "courted", [princess.q.name for princess in gawain.q.courted_princesses])
gawain.q.remove("courted_princesses", isolde)
print("after remove,", gawain.q.name, "courted", [princess.q.name for princess in gawain.q.courted_princesses])

gawain.q.relation("courted_princesses").add("p3")
print("fluent add via relation(...):", [princess.q.name for princess in gawain.q.courted_princesses])
gawain.q.relation("courted_princesses").remove("p3")
print("fluent remove via relation(...):", [princess.q.name for princess in gawain.q.courted_princesses])
