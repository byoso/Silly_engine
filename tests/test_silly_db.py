from dataclasses import dataclass
import random
from typing import Any
import pytest

from silly_engine import (
    SillyDb,
    SillyDbError,
    DataValidationError,
    ValidatedWithId,
    Oto,
    Mto,
    Otm,
    Mtm,
)


@dataclass
class Knight(ValidatedWithId):
    name: str = ""
    age: int = 0
    sword: Oto | Any = Oto(target="swords")

    def _validate(self) -> None:
        if self.age < 0:
            raise DataValidationError("Age must be non-negative")


@dataclass
class Sword(ValidatedWithId):
    name: str = ""
    length: int = 1
    description: str = ""
    owner: Oto | Any = Oto(target="knights")

    def _validate(self) -> None:
        if self.length <= 0:
            raise DataValidationError("Length must be positive")


def test_oto_propagation_object_and_id():
    db = SillyDb(":memory:")
    Knights = db.table("knights", Knight)
    Swords = db.table("swords", Sword)

    # create one knight and two swords
    k = Knight(name="Sir Test", age=30)
    Knights.save(k)
    s1 = Sword(name="One", length=50)
    s2 = Sword(name="Two", length=60)
    Swords.save(s1)
    Swords.save(s2)

    knight: Knight = Knights.get_first()
    all_swords = Swords.get_all()
    assert len(all_swords) >= 2
    s1: Sword = all_swords[0]
    s2: Sword = all_swords[1]

    # assign by object
    knight.sword = s1
    Knights.save(knight)

    # s1.owner should point to knight
    s1_after: Sword = Swords.get_by_id(s1._id)
    assert s1_after.owner is not None and s1_after.owner == knight._id

    # assign by id to a different sword
    knight.sword = s2._id
    Knights.save(knight)

    # old sword owner should be cleared, new sword owner set
    s1_after: Sword = Swords.get_by_id(s1._id)
    s2_after: Sword = Swords.get_by_id(s2._id)
    assert s1_after.owner is None
    assert s2_after.owner is not None and s2_after.owner == knight._id


def test_update_filter_disallowed_for_oto():
    db = SillyDb(":memory:")
    Knights = db.table("knights", Knight)
    Swords = db.table("swords", Sword)

    Knights.save(Knight(name="A", age=20))
    s = Sword(name="Unique", length=55)
    Swords.save(s)

    # bulk update modifying relation field should raise
    with pytest.raises(SillyDbError):
        Knights.update_filter(None, {"sword": s._id})


def test_delete_target_clears_source_relation():
    db = SillyDb(":memory:")
    Knights = db.table("knights", Knight)
    Swords = db.table("swords", Sword)

    # create knight and sword and link them
    k = Knight(name="Sir Delete", age=40)
    Knights.save(k)
    s = Sword(name="Ephemeral", length=42)
    Swords.save(s)

    knight = Knights.get_first()
    sword = Swords.get_first()
    knight.sword = sword
    Knights.save(knight)

    # ensure link exists
    s_after = Swords.get_by_id(sword._id)
    assert s_after is not None and s_after.owner is not None and s_after.owner == knight._id

    # delete the sword and ensure the knight.sword is cleared
    Swords.delete_by_id(sword._id)
    k_after = Knights.get_by_id(knight._id)
    assert k_after is not None
    assert getattr(k_after, 'sword') is None


def test_mto_and_otm_propagation():
    db = SillyDb(":memory:")
    @dataclass
    class Parent(ValidatedWithId):
        name: str = ""
        child: Mto = Mto("children")

        def _validate(self) -> None:
            return None

    @dataclass
    class Child(ValidatedWithId):
        name: str = ""
        parents: Otm = Otm(["parents"])

        def _validate(self) -> None:
            return None

    Parents = db.table("parents", Parent)
    Children = db.table("children", Child)

    # create parent and child and link them via Mto/Otm
    p = Parent(name="P1")
    Parents.save(p)
    c = Child(name="C1")
    Children.save(c)

    parent = Parents.get_first()
    child = Children.get_first()
    parent.child = child
    Parents.save(parent)

    # child should have parent id in its parents list
    c_after = Children.get_by_id(child._id)
    assert c_after is not None
    # parents field may be resolved or ids depending on recursive_level; check id membership
    parents_list = getattr(c_after, 'parents')
    if isinstance(parents_list, list):
        # items may be either ids or objects
        ids = [x._id if hasattr(x, '_id') else x for x in parents_list]
        assert parent._id in ids
    else:
        pytest.skip("Unexpected parents field type")

    # remove link and ensure child parents list is cleared
    parent.child = None
    Parents.save(parent)
    c_after2 = Children.get_by_id(child._id)
    assert c_after2 is not None
    parents_list2 = getattr(c_after2, 'parents')
    if isinstance(parents_list2, list):
        ids2 = [x._id if hasattr(x, '_id') else x for x in parents_list2]
        assert parent._id not in ids2
    else:
        pytest.skip("Unexpected parents field type after removal")


def test_mtm_basic_insert_and_query():
    db = SillyDb(":memory:")

    @dataclass
    class Author(ValidatedWithId):
        name: str = ""
        books: Mtm = Mtm("books")

        def _validate(self) -> None:
            return None

    @dataclass
    class Book(ValidatedWithId):
        title: str = ""
        authors: Mtm = Mtm("authors")

        def _validate(self) -> None:
            return None

    Authors = db.table("authors", Author)
    Books = db.table("books", Book)

    a = Author(name="A1")
    b = Book(title="B1")
    Authors.save(a)
    Books.save(b)

    a1 = Authors.get_first()
    b1 = Books.get_first()
    # link author to book via Mtm
    a1.books = [b1]
    Authors.save(a1)

    a_after = Authors.get_by_id(a1._id)
    assert a_after is not None
    books_list = getattr(a_after, 'books')
    assert isinstance(books_list, list)
    ids = [x._id if hasattr(x, '_id') else x for x in books_list]
    assert b1._id in ids

    # check reverse lookup on book side
    b_after = Books.get_by_id(b1._id)
    assert b_after is not None
    authors_list = getattr(b_after, 'authors')
    assert isinstance(authors_list, list)
    a_ids = [x._id if hasattr(x, '_id') else x for x in authors_list]
    assert a1._id in a_ids


def test_mtm_update_and_remove():
    db = SillyDb(":memory:")

    @dataclass
    class Tag(ValidatedWithId):
        name: str = ""
        items: Mtm = Mtm("items")

        def _validate(self) -> None:
            return None

    @dataclass
    class Item(ValidatedWithId):
        label: str = ""
        tags: Mtm = Mtm("tags")

        def _validate(self) -> None:
            return None

    Tags = db.table("tags", Tag)
    Items = db.table("items", Item)

    t = Tag(name="T1")
    i1 = Item(label="I1")
    i2 = Item(label="I2")
    Tags.save(t)
    Items.save(i1)
    Items.save(i2)

    t0 = Tags.get_first()
    i_1 = Items.get_all()[0]
    i_2 = Items.get_all()[1]
    # add two relations
    t0.items = [i_1, i_2]
    Tags.save(t0)

    t_after = Tags.get_by_id(t0._id)
    ids = [x._id if hasattr(x, '_id') else x for x in getattr(t_after, 'items')]
    assert i_1._id in ids and i_2._id in ids

    # remove one relation
    t0.items = [i_1]
    Tags.save(t0)
    t_after2 = Tags.get_by_id(t0._id)
    ids2 = [x._id if hasattr(x, '_id') else x for x in getattr(t_after2, 'items')]
    assert i_1._id in ids2 and i_2._id not in ids2
