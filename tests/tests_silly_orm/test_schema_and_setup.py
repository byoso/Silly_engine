def test_auto_creates_canonical_mtm_table_and_skips_mtm_column(orm_tables):
    db, *_ = orm_tables

    tables = [row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    assert "_mtm_courted_princesses__knights" in tables

    knight_columns = [
        row[1]
        for row in db.execute("PRAGMA table_info(knights)").fetchall()
    ]
    assert "courted_princesses_ids" not in knight_columns
    assert "dragons_killed_ids" not in knight_columns
    assert "name" in knight_columns
    assert "age" in knight_columns


def test_auto_creates_indexes_for_mto_oto_and_mtm(orm_tables):
    db, *_ = orm_tables

    knight_indexes = [
        row[1]
        for row in db.execute("PRAGMA index_list(knights)").fetchall()
    ]
    dragon_indexes = [
        row[1]
        for row in db.execute("PRAGMA index_list(dead_dragons)").fetchall()
    ]
    mtm_indexes = [
        row[1]
        for row in db.execute("PRAGMA index_list(_mtm_courted_princesses__knights)").fetchall()
    ]

    assert "idx_knights_sword_id" in knight_indexes
    assert "idx_dead_dragons_killer_id" in dragon_indexes
    assert "idx__mtm_courted_princesses__knights_knights_id" in mtm_indexes
    assert "idx__mtm_courted_princesses__knights_courted_princesses_id" in mtm_indexes
