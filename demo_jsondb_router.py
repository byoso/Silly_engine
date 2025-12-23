#! /usr/bin/env python3

"""
Little demo of the use of both the JsonDb (and migrations) and the router.

In this example, the databases are used with autosave=True, if you use it False, you will have to use db.save() after
each writting transaction.

"""

from dataclasses import dataclass, asdict
from datetime import datetime

from silly_engine.router import Router, RouterError
from silly_engine.jsondb import JsonDb, Collection
from silly_engine.minuit import AutoArray
from demo_migrations import mig_1_0_0, mig_2_0_0

@dataclass
class Person:
    name : str
    age: int
    time: str = str(datetime.now())



# db: JsonDb = JsonDb("test.json", autosave=True)

db: JsonDb = JsonDb("data.json", autosave=True, version="0.0.0", migrations={
    # play with the migrations: change the db version to see how it goes
    "1.0.0": mig_1_0_0,
    "2.0.0": mig_2_0_0,
})
# the reserved collection '_settings' is meant to be used with the migrations,
# it is to be used as a singleton (use .first(), .first_update(<data>))
# if you want to add other infos than 'version' but keep 'version' in !
Settings: Collection = db.collection("_settings")
Queries: Collection = db.collection("queries")
Persons: Collection = db.collection("persons")


def with_query(**kwargs):
    """
    You must had query parameters to make it work, e.g:
    test 1 ?foo=bar+foofoo=barbar.
    note that **kwargs is required to accept query params (it would be the same to accept a 'context')
    """
    print(kwargs)
    Queries.insert(kwargs.get("query_params", {}))
    db.save()

def infos():
    print(Settings.first())
    print(db.show())
    print(Persons.show())
    print(Queries.show())

def person_get(obj_id: str):
    print(Persons.get(obj_id))

def person(name, age):
    person = Person(name=name, age=age)
    Persons.insert(asdict(person))
    db.save()

def list_collection(collection_name):
    collection = db.collection(collection_name)
    if collection_name == "persons":
        exclusion = ["time"]
    else:
        exclusion = ["_id"]
    print(AutoArray(collection.all(), exclude=exclusion))

def drop_collection(collection_name):
    db.drop(collection_name)

def settings():
    print(Settings.first())
    print("--settings--")


router = Router(name="test router")
router.add_routes([
    "test",
    [["", "-h", "--help"], router.display_help, "display this help"],
    ["query", with_query, "query_params test (e.g: query?foo=bar+oof=rab)"],
    ["infos", infos, "infos about the database"],
    ["person <name:str> <age:int>", person, "create a test object"],
    ["list <collection_name:str>", list_collection, "list the items in the collection 'persons' or 'queries'"],
    ["drop <collection_name:str>", drop_collection, "drop the collection 'persons' or 'queries'"],
    ["person get <obj_id:str>", person_get, "get one Person from its _id"],
    ["settings", settings, "get settings"],
])


if __name__ == "__main__":
    try:
        router.query()
    except RouterError as e:
        print(f"Error: {e}")
