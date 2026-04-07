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

def mig_1_0_0(db):
    print("this is a fake migration... version db version is now 1.0.0")

def mig_1_1_0(db):
    print("this is a fake migration... version db version is now 1.1.0")

db = SillyDb("DB.sqlite3")

db.migrate([
    ("1.0.0", mig_1_0_0),
    ("1.1.0", mig_1_1_0),
])

Knights = db.table("knights", Knight)
Swords = db.table("swords", Sword)
DeadDragons = db.table("dead_dragons", DeadDragon)
CourtedPrincesses = db.table("courted_princesses", CourtedPrincess)




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


create_sample_data()
