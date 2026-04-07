from dataclasses import dataclass
import time

import pytest

from silly_engine.silly_orm.db import SillyDb
from silly_engine.silly_orm.models import Model


def test_meta_defaults_applied_on_insert():
    @dataclass
    class User(Model):
        username: str
        status: str = "pending"

        class Meta:
            defaults = {"status": "active"}

    db = SillyDb(":memory:")
    users = db.table("users", User)

    users.insert({"username": "alice"})
    alice = users.get(username="alice")

    assert alice.obj.status == "active"


def test_meta_auto_now_add_on_insert():
    @dataclass
    class Event(Model):
        name: str

        class Meta:
            auto_now_add = ["created_at"]

    db = SillyDb(":memory:")
    events = db.table("events", Event)

    before = int(time.time())
    events.insert({"name": "meeting"})
    after = int(time.time())

    event = events.filter(name="meeting").first()
    created_ts = event._data.get("_created_at")

    assert created_ts is not None
    assert before <= created_ts <= after


def test_meta_auto_now_on_update():
    @dataclass
    class Post(Model):
        title: str

        class Meta:
            auto_now = ["updated_at"]

    db = SillyDb(":memory:")
    posts = db.table("posts", Post)

    posts.insert({"_id": "p1", "title": "First"})
    time.sleep(0.1)
    before_update = int(time.time())
    posts.update("p1", title="Updated")
    after_update = int(time.time())

    post = posts.get(_id="p1")
    updated_ts = post._data.get("_updated_at")

    assert updated_ts is not None
    assert before_update <= updated_ts <= after_update


def test_meta_ordering_applied_automatically():
    @dataclass
    class Score(Model):
        player: str
        points: int

        class Meta:
            ordering = ["-points"]

    db = SillyDb(":memory:")
    scores = db.table("scores", Score)

    scores.insert({"player": "alice", "points": 100})
    scores.insert({"player": "bob", "points": 50})
    scores.insert({"player": "charlie", "points": 75})

    results = scores.filter().all()
    points = [r.obj.points for r in results]

    assert points == [100, 75, 50]


def test_meta_ttl_adds_expiry_field():
    @dataclass
    class Token(Model):
        value: str

        class Meta:
            ttl = 100

    db = SillyDb(":memory:")
    tokens = db.table("tokens", Token)

    tokens.insert({"_id": "t1", "value": "abc123"})
    token = tokens.get(_id="t1")

    assert "_expires_at" in token._data
    assert token._data["_expires_at"] > int(time.time())


def test_meta_ttl_filters_expired_records():
    @dataclass
    class Cache(Model):
        key: str
        value: str

        class Meta:
            ttl = 1

    db = SillyDb(":memory:")
    cache = db.table("cache", Cache)

    cache.insert({"_id": "c1", "key": "k1", "value": "v1"})

    assert cache.count() == 1
    assert cache.filter(key="k1").count() == 1

    time.sleep(1.5)

    assert cache.count() == 0
    assert cache.filter(key="k1").count() == 0


def test_meta_unique_constraint_enforced():
    @dataclass
    class Product(Model):
        sku: str
        name: str

        class Meta:
            unique = ["sku"]

    db = SillyDb(":memory:")
    products = db.table("products", Product)

    products.insert({"sku": "ABC123", "name": "Widget"})

    with pytest.raises(Exception):
        products.insert({"sku": "ABC123", "name": "Duplicate Widget"})


def test_meta_unique_multi_column():
    @dataclass
    class Slot(Model):
        day: str
        hour: int

        class Meta:
            unique = [["day", "hour"]]

    db = SillyDb(":memory:")
    slots = db.table("slots", Slot)

    slots.insert({"day": "monday", "hour": 9})

    with pytest.raises(Exception):
        slots.insert({"day": "monday", "hour": 9})

    slots.insert({"day": "monday", "hour": 10})
    assert slots.count() == 2


def test_meta_indexes_created():
    @dataclass
    class Article(Model):
        title: str
        author: str

        class Meta:
            indexes = ["author"]

    db = SillyDb(":memory:")
    db.table("articles", Article)

    db.connector.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='articles'"
    )
    index_names = [row[0] for row in db.connector.fetchall()]

    assert any("author" in idx for idx in index_names)


def test_meta_table_name_used_for_table():
    @dataclass
    class BlogPost(Model):
        title: str

        class Meta:
            table_name = "posts"

    db = SillyDb(":memory:")
    blog_posts = db.table(BlogPost)

    blog_posts.insert({"title": "Hello World"})
    post = blog_posts.first()
    assert post.obj.title == "Hello World"

    db.connector.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
    )
    assert db.connector.fetchone() is not None


def test_db_table_called_with_model_class_only():
    @dataclass
    class Comment(Model):
        body: str

    db = SillyDb(":memory:")
    comments = db.table(Comment)

    comments.insert({"body": "Nice ORM!"})
    comment = comments.first()
    assert comment.obj.body == "Nice ORM!"

    db.connector.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='comment'"
    )
    assert db.connector.fetchone() is not None
