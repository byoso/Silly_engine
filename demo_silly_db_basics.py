#!/usr/bin/env python3



from pathlib import Path
from pprint import pprint
from dataclasses import asdict, dataclass, field
from typing import List, Dict
import random


from silly_engine.silly_db import SillyDb
from silly_engine.data_validation import ValidatedWithId, DataValidationError

@dataclass
class Truc(ValidatedWithId):
    name: str = ""
    bar: int = 0
    enable: bool = False
    a_list: List[int] = field(default_factory=list)
    dico: Dict[str, int] = field(default_factory=dict)

    def _validate(self) -> None:
        if len(self.a_list) > 3:
            raise DataValidationError("Liste must not exceed 3 elements")

db = SillyDb("demoDatabase.sqlite3")
print("demoDatabase.sqlite3 created:", Path("demoDatabase.sqlite3").exists())


Trucs = db.table("trucs", Truc)

def create_random_truc(nbre: int = 1) -> Truc:
    names = ["toto", "tata", "titi", "tutu", "tete"]
    for i in range(nbre):
        truc = Truc(
            name=names[random.randint(0, len(names)-1)],
            bar=12,
            enable=bool(random.getrandbits(1)),
            a_list=[random.randint(1, 10) for _ in range(3)],
            dico={"a": random.randint(1, 10), "b": random.randint(1, 10)}
        )
        Trucs.add(truc)


trucs_data = [
    {
        "name": "toto", "bar": 12, "enable": False,
    },
    {
        "name": "tata", "bar": 12, "enable": True,
        "a_list": [1, 2, 3], "dico": {"a": 1, "b": 2}
    },
    {
        "name": "titi", "bar": 12, "enable": False,
        "a_list": [1, 2, 3, 4], "dico": {"a": 1, "b": 2}  # not validated by the Truc model (list > 3)
    }
]



# adding objects from dicts
for truc_data in trucs_data:
    try:
        truc = Truc(**truc_data)
        truc_dict = truc._dict
        Trucs.add(truc_dict)
        print("Truc to added:", truc_dict)
    except DataValidationError as e:
        print(f"Error adding truc {truc_data.get('name', 'unknown')}: {e}")

# adding objects from dataclass instances
try:
    truc_data = {
        "name": "tutu", "bar": 12, "enable": False,
        "a_list": [1, 2], "dico": {"a": 1}
    }
    truc = Truc(**truc_data)
    Trucs.add(truc)
    print("Truc to added:", truc._dict)
except DataValidationError as e:
    print(f"Error adding truc {truc_data.get('name', 'unknown')}: {e}")

# get_all
all_trucs = Trucs.get_all()
print("All trucs in database:")
for truc in all_trucs:
    print(truc)

# get_by_id
truc: Truc = all_trucs[-1]
print(f"Getting truc by id {truc._id}:")
try:
    truc_by_id = Trucs.get_by_id(truc._id)
    print(truc_by_id)
except Exception as e:
    print(f"Error getting truc by id: {e}")

# delete_by_id
truc_to_delete = all_trucs[:-3]
for truc in truc_to_delete:
    print(f"Deleting truc with id {truc._id}")
    try:
        Trucs.delete_by_id(truc._id)
        print(f"Truc with id {truc._id} deleted")
    except Exception as e:
        print(f"Error deleting truc by id: {e}")

pprint(Trucs.get_all())
print(Trucs.count())
pprint(Trucs._raw("SELECT *, bar FROM trucs"))
pprint(Trucs._get_raw("enable=1 AND name like '%toto%'"))

Trucs.delete_all()

create_random_truc(20)

# get_filter
print("\n GET FILTER TEST \n")
filtered_trucs = Trucs.get_filter(["enable=1", "name like '%to%'"])
print("Filtered trucs (enable=1, name like '%to%'):")
print(len(filtered_trucs), "trucs found")
for truc in filtered_trucs:
    print(truc)

Trucs.delete_all()

# Update
print("\n UPDATE TEST \n")
trucs = [Truc(name=f"truc_{i}", bar=5-i, enable=bool(random.getrandbits(1))) for i in range(5)]
for truc in trucs:
    Trucs.add(truc)
input("ENTER to continue...")

# update one
truc = Trucs.get_filter(["name='truc_3'"])[0]
print("truc before update:")
print(truc)
truc.name = "updated_truc"
truc.bar = 99
truc.enable = True
Trucs.update_one(truc)
new_truc = Trucs.get_by_id(truc._id)
print("Truc after update:")
print(new_truc)

input("ENTER to continue...")

# update filter
print("\n UPDATE FILTER TEST \n")
Trucs.update_filter(["enable=1"], {"name": "updated_name_by_filter", "bar": 42})
print("check the db manually to see the changes")