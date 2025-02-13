#! /usr/bin/env python3

"""
Use a json file as a database, read the docstrings to know more.

e.g.:
from jsondb import JsonDB

db = JsonDB(
    "data.json",
    autosave=True
    )

Truc = db.table("Truc")
Machin = db.table("Machin")

object1 = Truc.add({"name": "machin", "age": 12})
object2 = Truc.add({"name": "bidule", "age": 18})

id = object1.id

print(Truc.get(id))

"""


import json
import os
import uuid


class JsonDBError(Exception):
    pass


class JsonDB:
    """Interface with a json file"""

    def __init__(self, file=None, autosave=False):
        self.is_autosaving = autosave
        self.file = file
        self.tables = {}

        if os.path.exists(self.file):
            self.load()

    def __repr__(self):
        table_count = len(self.tables)
        return f"<JsonDB({self.file}) tables: {table_count} >"

    def _autosave(self):
        """Save the database if autosave is enabled"""
        if self.is_autosaving:
            self.save()

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = Table(name, self)
            self._autosave()
            return self.tables[name]
        else:
            return self.tables[name]

    def save(self):
        if self.file is None:
            return
        data = {}
        for table in self.tables:
            data[table] = {}
            for id in self.tables[table].data:
                data[table][id] = self.tables[table].data[id].data
        with open(self.file, 'w') as file:
            json.dump(data, file, indent=2)

    def load(self):
        if self.file is None:
            return
        if os.path.exists(self.file):
            with open(self.file, 'r') as file:
                data = json.load(file)
            for table_name in data:
                new_table = self.table(table_name)
                for id in data[table_name]:
                    new_table.add(data[table_name][id], id)

    def display(self):
        tables_count = len(self.tables)
        display = '\n+'+'-'*54 + "+\n"
        display += f"|*-- JsonDB --* file: {self.file} - tables: {tables_count:<13}|\n"
        display += f"| {'Tables':40} | {'Item(s)':10}|\n"
        display += '+'+'-'*54 + "+\n"

        for table in self.tables:
            item_count = len(self.tables[table].data)
            display += f"| {table:40} | {item_count:10}|\n"
        display += '+'+'-'*54 + "+\n"
        return display

    def drop(self, table_name):
        """Delete a table and all its items"""
        if table_name in self.tables:
            del self.tables[table_name]
            self._autosave()


class Table:
    """Collection of dictionnary objects"""
    def __init__(self, name, db):
        self.database = db
        self.name = name
        self.data = {}

    def __repr__(self):
        return f"<{self.name} - objects in table: {len(self.data)} >"

    def _autosave(self):
        if self.database.is_autosaving:
            self.database.save()

    def add(self, input_data: dict, id=None):
        """Add an item to the table"""
        item = Item(input_data, self, id=id)
        self.data[item.id] = item
        self._autosave()
        return item

    def all(self):
        """Returns all the items of the table"""
        return self.query(lambda x: True)

    def all_objects(self):
        """Returns all the items of the table"""
        return self.data

    def display(self):
        """Fancy representation of the table and its items
        e.g.: print(Table.display())
        """
        display = '\n+'+'-'*55 + "+\n"
        display += f"|*-- Table: {self.name} --* items: {len(self.data):<28}|\n"
        for id in self.data:
            display += f"| {id:<53} |\n"
        display += f"|*-- Table: {self.name} --* items: {len(self.data):<28}|\n"
        display += '+'+'-'*55 + "+\n"
        return display

    def first(self):
        """Returns the first item of the table or None if the table is empty"""
        if len(self.data) == 0:
            return None
        for id in self.data:
            return self.data[id].data

    def first_object(self):
        """Returns the first item of the table or None if the table is empty"""
        if len(self.data) == 0:
            return None
        for id in self.data:
            return self.data[id]

    def get(self, key: str):
        """Get a unique item dict from its id"""
        if key in self.data:
            return self.data[key].data

    def get_object(self, key: str):
        """Get a unique item from its id"""
        if key in self.data:
            return self.data[key]

    def query(self, query_func=None):
        """Takes one parameter function that returns a boolean value
        example: queryset = Table.query(lambda x: x['age'] > 18)

        returns a dict of datas.
        """
        queryset = []
        for id in self.data:
            try:
                if query_func(self.data[id].data):
                    queryset.append(self.data[id].data)
            except KeyError:
                continue
        return queryset

    def query_objects(self, query_func=None):
        """Takes one parameter function that returns a boolean value
        example: queryset = Table.query(lambda x: x['age'] > 18)

        returns a list of Item objects.
        """
        queryset = []
        for id in self.data:
            try:
                if query_func(self.data[id].data):
                    queryset.append(self.data[id])
            except KeyError:
                continue
        return queryset

    def query_delete(self, query_func=None):
        """Takes one parameter function that returns a boolean value
        example: Table.query_delete(lambda x: x['age'] > 18)
        """
        to_delete = []
        for id in self.data:
            item = self.data[id]
            try:
                if query_func(item.data):
                    to_delete.append(item)
            except KeyError:
                continue
        for item in to_delete:
            item.delete()
        self._autosave()


class Item:
    def __init__(self, data, table, id=None):
        self.id = id
        if id is None:
            self.id = str(uuid.uuid4())
        self.table = table
        self.data = data
        self.data['_id'] = self.id

    def __repr__(self):
        return f"<{self.id}: {self.data}>"

    def _autosave(self):
        if self.table.database.is_autosaving:
            self.table.database.save()

    def set(self, *args: tuple):
        """args are tuples of (key, value)"""
        for arg in args:
            if not type(arg) is tuple:
                raise JsonDBError('expected argument type is tuple')
            self.data[arg[0]] = arg[1]
        self._autosave()
        return self

    def del_attr(self, *args: str):
        for arg in args:
            if not type(arg) is str:
                raise JsonDBError('expected argument type is str')
            if arg in self.data:
                del self.data[arg]
                self._autosave()
        return self

    def delete(self):
        del self.table.data[self.id]
        self._autosave()
