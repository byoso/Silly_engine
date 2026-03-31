"""
This file is an example of how should look the migrations.
Each migration must have the database as parameter.
"""


from silly_engine import JsonDb


def mig_1_0_0(db: JsonDb):
    """Add a 'test' key to each query item."""
    Queries = db.collection("queries")
    for item in Queries.all():
        # item is an Item instance; use its update method
        item.update({"test": "this"})


def mig_2_0_0(db: JsonDb):
    """Rename 'foo' key to 'name' on query items when present."""
    Queries = db.collection("queries")
    for item in Queries.all():
        data = item.data
        if data.get("foo") is not None:
            # move foo -> name
            data["name"] = data.pop("foo")
            item.update(data)
