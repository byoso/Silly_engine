"""
This file is an example of how should look the migrations.
Each migration must have the database as parameter.
"""


from silly_engine import JsonDb


def mig_1_0_0(db: JsonDb):
    Queries = db.collection("queries")
    for query in Queries.all():
        query["test"] = "this"
        Queries.update(query)

def mig_2_0_0(db: JsonDb):
    Queries = db.collection("queries")
    for query in Queries.all():
        if query.get("foo", None) is not None:
            query["name"] = query.pop("foo")
            Queries.update(query)
