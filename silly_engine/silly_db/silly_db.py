"""
version:
- 1.0.0: That works !
A simple ORM for SQLite databases, with support for dataclass models and basic data validation.
Expected to work with dataclasses.
"""
from __future__ import annotations
from contextlib import contextmanager
import sqlite3
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, is_dataclass, asdict, MISSING
from typing import Any, Callable, Generic, Type, TypeVar, Tuple, get_origin, get_type_hints
from uuid import uuid4

from .models import SillyOrmRelation, Oto, Mto, Otm, Mtm

DEFAULT_PAGE_SIZE = 1000

ModelT = TypeVar('ModelT')


def is_relation_field(field_name: str, relations: dict[str, SillyOrmRelation]) -> bool:
    return field_name in relations


class SillyDbError(Exception):
    pass

@dataclass
class Settings:
    _id: str = field(init=True, default_factory=lambda: str(uuid4()))
    version: str = ""
    description: str = ""


class SillyDb:
    def __init__(
            self, db_path: str,
            description: str = "Silly ORM database",
            recursive_level: int = 0,
            migrations: list[Tuple[str, Callable]] | None = None
            )-> None:
        self.db_path = Path(db_path)
        self.tables: dict[str, Table] = {}
        self.recursive_level = recursive_level
        with self._transaction():
            try:
                self.conn = sqlite3.connect(str(self.db_path))
                self.cursor = self.conn.cursor()
                self._connected = True
            except sqlite3.Error as e:
                raise SillyDbError(f"Unable to open database '{db_path}': {e}") from e

        self._settings = self.table("_settings", Settings)
        if self._settings.count() == 0:
            settings = Settings(description=description, version="0.0.0")
            self._settings.register(settings)
        if migrations is not None:
            self.migrate(migrations)

    def migrate(self, migrations: list[Tuple[str, Callable]]) -> None:
        if migrations is not None:
            for migration in migrations:
                settings_table = self.tables.get("_settings")
                if settings_table is None:
                    return
                settings: Settings | None = settings_table.get_first()
                assert settings is not None
                current_version = tuple(int(x) for x in settings.version.split(".")) if settings_table.count() > 0 else (0, 0, 0)
                migration_version = tuple(int(x) for x in migration[0].split("."))
                if migration_version > current_version:
                    try:
                        migration[1](self)
                        # update version in settings after successful migration
                        settings.version = migration[0]
                        settings_table.save(settings)
                    except Exception as e:
                        raise SillyDbError(f"Migration {migration[0]} failed: {e}") from e

    def drop(self, table_name: str) -> None:
        with self._transaction():
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        # Remove from tables dict if it exists
        if table_name in self.tables:
            del self.tables[table_name]

    def table(self, name: str, model: Type[ModelT] | Any,
            singleton: bool = False) -> Table[ModelT]:
        """model should be a dataclass"""
        table = Table(self, name, model, singleton=singleton)
        self.tables[name] = table
        return table

    @contextmanager
    def _transaction(self):
        try:
            yield self
            if getattr(self, "conn", None):
                self.conn.commit()
        except Exception:
            if getattr(self, "conn", None):
                try:
                    self.conn.rollback()
                except Exception:
                    pass
            raise SillyDbError("Transaction failed and was rolled back")


    def _close(self) -> None:
        """
        Explicitely close the database connection and cursor, if they exist.
        Should not be used, use the '_transaction' context manager instead.
        """
        if getattr(self, "cursor", None):
            try:
                self.cursor.close()
            except Exception:
                pass
        if getattr(self, "conn", None):
            try:
                self.conn.close()
            except Exception:
                pass
        self._connected = False

    def delete_all_tables(self) -> None:
        """Supprime toutes les entrées de toutes les tables, sauf _settings."""
        try:
            with self._transaction():
                # lister toutes les tables existantes dans la DB SQLite
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                table_rows = [r[0] for r in self.cursor.fetchall()]
                for tbl in table_rows:
                    if tbl == "_settings":
                        continue
                    try:
                        self.cursor.execute(f"DELETE FROM {tbl}")
                    except sqlite3.OperationalError:
                        # ignorer tables impossibles à effacer pour quelque raison
                        pass
        except Exception as e:
            raise SillyDbError(f"Failed to delete all table rows: {e}") from e

    def _destroy(self) -> None:
        """Close connection and delete the database file. Use with caution."""
        self._close()
        try:
            if self.db_path.exists():
                self.db_path.unlink()
        except Exception as e:
            raise SillyDbError(f"Failed to delete database file '{self.db_path}': {e}") from e

class Table(Generic[ModelT]):
    def __init__(
            self, db: SillyDb, name: str, model: Type[ModelT] | Any,
            singleton: bool = False) -> None:
        self.db = db
        self.name = name
        self.model = model
        self.singleton = singleton
        assert is_dataclass(self.model)
        self._field_types = {}
        # relation name -> SillyOrmRelation instance (e.g. Oto)
        self._relations: dict[str, SillyOrmRelation] = {}
        # Create table if not exists
        columns = []
        has_text_pk = False
        type_hints = get_type_hints(self.model)
        for field in self.model.__dataclass_fields__.values():
            field_type = type_hints.get(field.name, field.type)
            # detect relation default on the dataclass field (e.g. sword: Oto = Oto(target="swords"))
            default = getattr(field, "default", MISSING)
            if default is not MISSING and isinstance(default, SillyOrmRelation):
                # register relation metadata and store underlying column as TEXT
                self._relations[field.name] = default
                # Otm/Mtm store lists of ids; treat their python type as list
                if isinstance(default, (Otm, Mtm)):
                    self._field_types[field.name] = list
                else:
                    self._field_types[field.name] = str
                # Mtm relations are stored in a join table, not as a column on the source table
                if isinstance(default, Mtm):
                    # do not create a column for Mtm
                    continue
                if field.name == "_id":
                    columns.append("_id TEXT PRIMARY KEY")
                    has_text_pk = True
                else:
                    columns.append(f"{field.name} TEXT")
                continue

            # fallback: if annotation itself is a SillyOrmRelation type, store as TEXT
            try:
                if isinstance(field_type, type) and issubclass(field_type, SillyOrmRelation):
                    self._field_types[field.name] = str
                    columns.append(f"{field.name} TEXT")
                    continue
            except Exception:
                pass

            # regular type handling
            self._field_types[field.name] = field_type
            if field.name == "_id":
                columns.append("_id TEXT PRIMARY KEY")
                self._field_types[field.name] = field_type
                has_text_pk = True
                continue
            origin = get_origin(field_type)
            if field_type == int:
                sql_type = "INTEGER"
            elif field_type == str:
                sql_type = "TEXT"
            elif field_type == bool:
                sql_type = "INTEGER"
            elif field_type == float:
                sql_type = "REAL"
            elif field_type == dict or origin == dict:
                sql_type = "TEXT"
            elif field_type == list or origin == list:
                sql_type = "TEXT"
            else:
                raise TypeError(f"Unsupported field type: {field_type} for field '{field.name}' in model '{self.model.__name__}'")
            columns.append(f"{field.name} {sql_type}")
        columns_sql = ", ".join(columns)
        if has_text_pk:
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({columns_sql})"
        else:
            create_table_sql = (
                f"CREATE TABLE IF NOT EXISTS {self.name} "
                f"(id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_sql})"
        )
        with self.db._transaction():
            self.db.cursor.execute(create_table_sql)
            # ensure any missing columns (schema drift) are added to existing table
            try:
                # get existing columns
                self.db.cursor.execute(f"PRAGMA table_info({self.name})")
                existing = [r[1] for r in self.db.cursor.fetchall()]
                for col_def in columns:
                    col_name = col_def.split()[0]
                    if col_name not in existing:
                        # add missing column (use the type declared)
                        self.db.cursor.execute(f"ALTER TABLE {self.name} ADD COLUMN {col_def}")
            except Exception:
                # if PRAGMA/ALTER fails, ignore and proceed — table may be locked or read-only
                pass
            if has_text_pk:
                # create trigger to prevent _id updates
                trigger_sql = (
                    f"CREATE TRIGGER IF NOT EXISTS prevent_id_update_{self.name} "
                    f"BEFORE UPDATE ON {self.name} \n"
                    "BEGIN \n"
                    "  SELECT CASE WHEN NEW._id IS NOT OLD._id \n"
                    "    THEN RAISE(ABORT, 'Cannot modify _id') \n"
                    "END;\n"
                    "END;\n"
                )
                self.db.cursor.execute(trigger_sql)
            # create join tables for any Mtm relations declared on this model
            try:
                for rn, rel in self._relations.items():
                    if isinstance(rel, Mtm):
                        # join table name: {source}_{field}_{target}
                        target = getattr(rel, 'target', None) if getattr(rel, 'target', None) is not None else (rel.targets[0] if getattr(rel, 'targets', None) else None)
                        if not target:
                            continue
                        # canonical join table name independent of field naming
                        sname, tname = sorted([self.name, target])
                        join_name = f"_mtm_{sname}__{tname}"
                        # create join table with text ids and a uniqueness constraint
                        join_sql = (
                            f"CREATE TABLE IF NOT EXISTS {join_name} (src_id TEXT NOT NULL, tgt_id TEXT NOT NULL, "
                            f"UNIQUE(src_id, tgt_id))"
                        )
                        self.db.cursor.execute(join_sql)
                        # create indexes for faster lookups
                        try:
                            self.db.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{join_name}_src ON {join_name}(src_id)")
                            self.db.cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{join_name}_tgt ON {join_name}(tgt_id)")
                        except Exception:
                            pass
            except Exception:
                pass

    def __repr__(self) -> str:
        return f"<Table {self.name} ({self.model.__name__})>"

    def _propagate_oto(self, source_id: Any, field_name: str, new_target_id: Any, old_target_id: Any = None, _guard: set | None = None) -> None:
        """
        Propagate a one-to-one `Oto` relation change from this table (source) to the target table.

        - `source_id`: id or _id of the source object being changed
        - `field_name`: name of the relation field on the source table
        - `new_target_id`: id of the new target object (or None to clear)
        - `old_target_id`: previous target id (if known)
        - `_guard`: set used to avoid circular propagation across reciprocal updates
        """
        if field_name not in self._relations:
            return
        if _guard is None:
            _guard = set()
        key = (self.name, field_name, source_id)
        if key in _guard:
            return
        _guard.add(key)

        rel = self._relations.get(field_name)
        if rel is None:
            return
        target_table = self.db.tables.get(rel.target)
        if target_table is None:
            return

        # find reverse fields on the target table that point back to this table
        reverse_fields = []
        for fn, r in target_table._relations.items():
            try:
                if getattr(r, 'target', None) == self.name:
                    reverse_fields.append(fn)
                    continue
            except Exception:
                pass
            # Otm may point to multiple targets via .targets
            try:
                if isinstance(r, Otm) and self.name in getattr(r, 'targets', []):
                    reverse_fields.append(fn)
            except Exception:
                pass

        # Clear reverse field on old target (if different)
        if old_target_id is not None and old_target_id != new_target_id:
            for rf in reverse_fields:
                rmeta = target_table._relations.get(rf)
                try:
                    if isinstance(rmeta, Otm):
                        # remove source_id from target's list
                        id_col = "_id" if "_id" in target_table._field_types else "id"
                        with self.db._transaction():
                            self.db.cursor.execute(f"SELECT {rf} FROM {target_table.name} WHERE {id_col} = ?", (old_target_id,))
                            row = self.db.cursor.fetchone()
                        if row is not None and row[0] is not None:
                            try:
                                lst = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                            except Exception:
                                lst = [row[0]]
                            if source_id in lst:
                                lst = [x for x in lst if x != source_id]
                                try:
                                    target_table._update_by_id(old_target_id, {rf: lst}, _propagate=False, _guard=_guard)
                                except Exception:
                                    pass
                    else:
                        target_table._update_by_id(old_target_id, {rf: None}, _propagate=False, _guard=_guard)
                except Exception:
                    pass

        # Enforce uniqueness on source table: remove other source rows pointing to the same new_target_id
        if new_target_id is not None:
            source_id_col = "_id" if "_id" in self._field_types else "id"
            with self.db._transaction():
                try:
                    self.db.cursor.execute(
                        f"UPDATE {self.name} SET {field_name} = NULL WHERE {field_name} = ? AND {source_id_col} != ?",
                        (new_target_id, source_id),
                    )
                except Exception:
                    pass

        # Set reverse field on new target to point to source
        if new_target_id is not None:
            for rf in reverse_fields:
                rmeta = target_table._relations.get(rf)
                try:
                    if isinstance(rmeta, Otm):
                        # add source_id to target's list if not present
                        id_col = "_id" if "_id" in target_table._field_types else "id"
                        with self.db._transaction():
                            self.db.cursor.execute(f"SELECT {rf} FROM {target_table.name} WHERE {id_col} = ?", (new_target_id,))
                            row = self.db.cursor.fetchone()
                        if row is None:
                            continue
                        try:
                            lst = json.loads(row[0]) if isinstance(row[0], str) and row[0] is not None else (row[0] or [])
                        except Exception:
                            lst = [row[0]] if row[0] is not None else []
                        if source_id not in lst:
                            lst.append(source_id)
                            try:
                                # debug: updating Otm reverse list
                                # print to stderr to aid debugging in tests
                                print(f"_propagate_oto: adding {source_id} to {target_table.name}.{rf} on row {new_target_id}", file=sys.stderr)
                                target_table._update_by_id(new_target_id, {rf: lst}, _propagate=False, _guard=_guard)
                            except Exception:
                                pass
                    else:
                        target_table._update_by_id(new_target_id, {rf: source_id}, _propagate=False, _guard=_guard)
                except Exception:
                    pass

    # Mto behaves like Oto (many-to-one from source perspective). Delegate to _propagate_oto.
    def _propagate_mto(self, source_id: Any, field_name: str, new_target_id: Any, old_target_id: Any = None, _guard: set | None = None) -> None:
        return self._propagate_oto(source_id, field_name, new_target_id, old_target_id=old_target_id, _guard=_guard)

    def _propagate_otm_on_change(self, source_id: Any, field_name: str, new_list: list | None, old_list: list | None, _guard: set | None = None) -> None:
        """Propagate changes for an Otm (one-to-many list) field.

        Update reverse pointers on target rows when the list of target ids changes.
        """
        if field_name not in self._relations:
            return
        if _guard is None:
            _guard = set()
        key = (self.name, field_name, source_id)
        if key in _guard:
            return
        _guard.add(key)

        rel = self._relations.get(field_name)
        if rel is None:
            return
        # Otm.targets is a list of target table names; support single-target case
        targets = getattr(rel, "targets", None)
        if not targets:
            return
        # For now, handle the first target
        target_name = targets[0]
        target_table = self.db.tables.get(target_name)
        if target_table is None:
            return

        old_set = set(old_list or [])
        new_set = set(new_list or [])

        # removed ids: clear reverse fields on those targets
        removed = old_set - new_set
        added = new_set - old_set

        reverse_fields = [fn for fn, r in target_table._relations.items() if (getattr(r, 'target', None) == self.name)]

        for rf in reverse_fields:
            for tid in removed:
                try:
                    target_table._update_by_id(tid, {rf: None}, _propagate=False, _guard=_guard)
                except Exception:
                    pass
            for tid in added:
                try:
                    target_table._update_by_id(tid, {rf: source_id}, _propagate=False, _guard=_guard)
                except Exception:
                    pass

    def _sync_mtm_join(self, source_id: Any, field_name: str, new_list: list | None, old_list: list | None) -> None:
        """Synchronize the join table entries for an Mtm relation on this table.

        - source_id: id on this table
        - field_name: name of the Mtm field on this table
        - new_list/old_list: lists of target ids
        """
        rel = self._relations.get(field_name)
        if rel is None or not isinstance(rel, Mtm):
            return
        target = getattr(rel, 'target', None) if getattr(rel, 'target', None) is not None else (rel.targets[0] if getattr(rel, 'targets', None) else None)
        if not target:
            return
        join_name = self._find_mtm_join_name(field_name, target)
        new_set = set(new_list or [])
        old_set = set(old_list or [])
        to_add = new_set - old_set
        to_remove = old_set - new_set
        id_col = "_id" if "_id" in self._field_types else "id"
        # Use canonical join column ordering when writing to the join table.
        sname, tname = sorted([self.name, target])
        with self.db._transaction():
            for tid in to_remove:
                try:
                    # determine ordered pair for deletion
                    if sname == self.name:
                        src_val, tgt_val = source_id, tid
                    else:
                        src_val, tgt_val = tid, source_id
                    print(f"_sync_mtm_join: deleting from {join_name} ({src_val},{tgt_val})", file=sys.stderr)
                    self.db.cursor.execute(f"DELETE FROM {join_name} WHERE src_id = ? AND tgt_id = ?", (src_val, tgt_val))
                except Exception:
                    pass
            for tid in to_add:
                try:
                    if sname == self.name:
                        src_val, tgt_val = source_id, tid
                    else:
                        src_val, tgt_val = tid, source_id
                    print(f"_sync_mtm_join: inserting into {join_name} ({src_val},{tgt_val})", file=sys.stderr)
                    self.db.cursor.execute(f"INSERT OR IGNORE INTO {join_name} (src_id, tgt_id) VALUES (?, ?)", (src_val, tgt_val))
                except Exception:
                    pass

    def _find_mtm_join_name(self, field_name: str, target_name: str) -> str:
        # canonical join table name: mtm_{min(source,target)}_{max(source,target)}
        sname, tname = sorted([self.name, target_name])
        candidate = f"_mtm_{sname}__{tname}"
        try:
            with self.db._transaction():
                self.db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (candidate,))
                row = self.db.cursor.fetchone()
            if row:
                return candidate
        except Exception:
            pass
        # fallback: find any table containing both table names (created by the other side)
        try:
            pattern1 = f"%{self.name}%{target_name}%"
            pattern2 = f"%{target_name}%{self.name}%"
            with self.db._transaction():
                # debug: list all tables to help find join table
                try:
                    self.db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    all_tables = [r[0] for r in self.db.cursor.fetchall()]
                    print(f"_find_mtm_join_name: all tables = {all_tables}", file=sys.stderr)
                except Exception:
                    pass
                self.db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE ? OR name LIKE ?) LIMIT 1", (pattern1, pattern2))
                row = self.db.cursor.fetchone()
            if row:
                print(f"_find_mtm_join_name: found join table {row[0]} for patterns {pattern1} {pattern2}", file=sys.stderr)
                return row[0]
        except Exception:
            pass
        # default to candidate (it will be created if needed when syncing)
        return candidate

    def _raw(self, query: str) -> list[tuple]:
        with self.db._transaction():
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
        return rows

    def _get_raw(self, query: str) -> list[object]:
        with self.db._transaction():
            self.db.cursor.execute(f"SELECT * FROM {self.name} WHERE {query}")
            rows = self.db.cursor.fetchall()
        return rows

    def _get_raw_paginated(self, query: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[list[object], int, int, int]:
        offset = (page - 1) * page_size
        count_query = f"SELECT COUNT(*) FROM {self.name} WHERE {query}"
        with self.db._transaction():
            self.db.cursor.execute(count_query)
            count = self.db.cursor.fetchone()[0]
            self.db.cursor.execute(f"SELECT * FROM {self.name} WHERE {query} LIMIT ? OFFSET ?", (page_size, offset))
            rows = self.db.cursor.fetchall()
        return rows, page, page_size, count

    def _rows_to_models(self, rows: list[object], recursive_level: int | None = None) -> list[ModelT]:
        if recursive_level is None:
            recursive_level = self.db.recursive_level
        results = []
        for row in rows:
            assert isinstance(row, tuple), f"Expected row to be a tuple, got {type(row)}"
            obj_dict = {}
            pending_relations: dict[str, object] = {}
            # get stable column names from the DB schema to avoid cursor.description races
            col_names = []
            try:
                with self.db._transaction():
                    self.db.cursor.execute(f"PRAGMA table_info({self.name})")
                    info_rows = self.db.cursor.fetchall()
                col_names = [r[1] for r in info_rows]
            except Exception:
                # fallback to cursor.description if PRAGMA fails
                col_names = [c[0] for c in self.db.cursor.description] if self.db.cursor.description is not None else []
            for idx, col_name in enumerate(col_names):
                value = row[idx]
                # if this field is a registered relation, resolve it to the target object
                if col_name in self._relations:
                    rel = self._relations[col_name]
                    # Otm stores a list of ids (JSON) in the DB
                    if isinstance(rel, Otm):
                        if value is not None:
                            # parse stored JSON list or accept already-list values
                            try:
                                ids = json.loads(value) if isinstance(value, str) else value
                            except Exception:
                                ids = [value]
                            if recursive_level > 0:
                                effective = recursive_level
                                if recursive_level > 1:
                                    effective = 1
                                target_name = rel.targets[0] if getattr(rel, "targets", None) else None
                                target_table = self.db.tables.get(target_name) if target_name is not None else None
                                if target_table is not None and effective > 0:
                                    resolved = [target_table.get_by_id(i, recursive_level=effective - 1) for i in ids]
                                else:
                                    resolved = ids
                            else:
                                resolved = ids
                        else:
                            resolved = []
                        obj_dict[col_name] = rel
                        pending_relations[col_name] = resolved
                        continue

                    # Mtm is stored in a join table; fetch ids from join table
                    if isinstance(rel, Mtm):
                        target_name = rel.target if getattr(rel, 'target', None) is not None else (rel.targets[0] if getattr(rel, 'targets', None) else None)
                        ids = []
                        if target_name is not None:
                            join_name = self._find_mtm_join_name(col_name, target_name)
                            id_col = "_id" if "_id" in self._field_types else "id"
                            try:
                                # determine source id from current row using column names
                                id_col_name = "_id" if "_id" in col_names else ("id" if "id" in col_names else col_names[0])
                                src_idx = col_names.index(id_col_name)
                                source_id_val = row[src_idx]

                                # determine canonical ordering of join columns
                                sname, tname = sorted([self.name, target_name])
                                print(f"_mtm_read: querying join {join_name} for source {source_id_val} (sname={sname}, tname={tname})", file=sys.stderr)
                                with self.db._transaction():
                                    if sname == self.name:
                                        # join stored as (src_id=this table, tgt_id=target table)
                                        self.db.cursor.execute(f"SELECT tgt_id FROM {join_name} WHERE src_id = ?", (source_id_val,))
                                    else:
                                        # join stored as (src_id=other table, tgt_id=this table)
                                        self.db.cursor.execute(f"SELECT src_id FROM {join_name} WHERE tgt_id = ?", (source_id_val,))
                                    id_rows = self.db.cursor.fetchall()
                                ids = [r[0] for r in id_rows]
                            except Exception:
                                ids = []
                        if recursive_level > 0:
                            effective = recursive_level
                            if recursive_level > 1:
                                effective = 1
                            target_table = self.db.tables.get(target_name) if target_name is not None else None
                            if target_table is not None and effective > 0:
                                resolved = [target_table.get_by_id(i, recursive_level=effective - 1) for i in ids]
                            else:
                                resolved = ids
                        else:
                            resolved = ids
                        obj_dict[col_name] = rel
                        pending_relations[col_name] = resolved
                        continue

                    # resolve target object for single-target relations (Oto/Mto)
                    if value is not None:
                        if recursive_level > 0:
                            # cap resolution depth to 1 for Oto and Mto relations
                            effective = recursive_level
                            if isinstance(rel, (Oto, Mto)) and recursive_level > 1:
                                effective = 1
                            target_table = self.db.tables.get(getattr(rel, 'target', None))
                            if target_table is not None:
                                # pass down (effective - 1) to avoid deeper recursion
                                target_obj = target_table.get_by_id(value, recursive_level=effective - 1)
                            else:
                                target_obj = None
                        else:
                            # at depth 0, expose the stored id rather than None
                            target_obj = value
                    else:
                        target_obj = None
                    obj_dict[col_name] = rel
                    pending_relations[col_name] = target_obj
                    continue
                ftype = self._field_types.get(col_name)
                origin = get_origin(ftype) if ftype is not None else None
                if value is not None:
                    if ftype == bool:
                        obj_dict[col_name] = bool(value)
                    elif ftype == int:
                        obj_dict[col_name] = int(value)
                    elif ftype == float:
                        obj_dict[col_name] = float(value)
                    elif ftype == str:
                        obj_dict[col_name] = value
                    elif ftype == dict or origin == dict or ftype == list or origin == list:
                        try:
                            obj_dict[col_name] = json.loads(value)
                        except Exception:
                            obj_dict[col_name] = value
                    else:
                        # fallback: try JSON deserialization, otherwise keep as str
                        try:
                            obj_dict[col_name] = json.loads(value)
                        except Exception:
                            obj_dict[col_name] = value
                else:
                    obj_dict[col_name] = None
            # handle relations that do not have a column on this table (e.g., Mtm join-table relations)
            # print(f"_rows_to_models: handling non-column relations for table {self.name}", file=sys.stderr)
            for rn, rel in self._relations.items():
                if rn in obj_dict:
                    continue
                if isinstance(rel, Mtm):
                    target_name = rel.target if getattr(rel, 'target', None) is not None else (rel.targets[0] if getattr(rel, 'targets', None) else None)
                    ids = []
                    if target_name is not None:
                        join_name = self._find_mtm_join_name(rn, target_name)
                        try:
                            # determine source id from current row using column names
                            id_col_name = "_id" if "_id" in col_names else ("id" if "id" in col_names else col_names[0])
                            src_idx = col_names.index(id_col_name)
                            source_id_val = row[src_idx]
                            # determine canonical ordering
                            sname, tname = sorted([self.name, target_name])
                            with self.db._transaction():
                                if sname == self.name:
                                    self.db.cursor.execute(f"SELECT tgt_id FROM {join_name} WHERE src_id = ?", (source_id_val,))
                                else:
                                    self.db.cursor.execute(f"SELECT src_id FROM {join_name} WHERE tgt_id = ?", (source_id_val,))
                                id_rows = self.db.cursor.fetchall()
                            ids = [r[0] for r in id_rows]
                        except Exception:
                            ids = []
                    if recursive_level > 0:
                        effective = recursive_level
                        if recursive_level > 1:
                            effective = 1
                        target_table = self.db.tables.get(target_name) if target_name is not None else None
                        if target_table is not None and effective > 0:
                            resolved = [target_table.get_by_id(i, recursive_level=effective - 1) for i in ids]
                        else:
                            resolved = ids
                    else:
                        resolved = ids
                    obj_dict[rn] = rel
                    pending_relations[rn] = resolved

            try:
                # Filter out DB columns that are not dataclass fields (e.g., autoincrement 'id')
                allowed = set(self.model.__dataclass_fields__.keys())
                filtered = {k: v for k, v in obj_dict.items() if k in allowed}
                obj = self.model(**filtered)
                # attach resolved relation objects after construction (bypass validation)
                for rn, rv in pending_relations.items():
                    setattr(obj, rn, rv)
                results.append(obj)
            except Exception as e:
                raise SillyDbError(f"Error deserializing row {row} from table '{self.name}': {e}") from e
        return results

    def delete_all(self) -> None:
        with self.db._transaction():
            self.db.cursor.execute(f"DELETE FROM {self.name}")

    def delete_by_id(self, id_value: Any) -> None:
        id_col = "_id" if "_id" in self._field_types else "id"

        # Before deleting this target row, clear any Oto references pointing to it
        # from other tables (set the source relation field to NULL) so objects
        # referencing this target get their relation cleared.
        for table in list(self.db.tables.values()):
            # skip if same table (self) — still handle if self has relations pointing to itself
            for rel_field, rel in table._relations.items():
                try:
                    if rel.target != self.name:
                        continue
                except Exception:
                    continue

                # find rows in the source table that reference this target id
                src_id_col = "_id" if "_id" in table._field_types else "id"
                with self.db._transaction():
                    self.db.cursor.execute(f"SELECT {src_id_col} FROM {table.name} WHERE {rel_field} = ?", (id_value,))
                    rows = self.db.cursor.fetchall()
                for row in rows:
                    src_id = row[0]
                    try:
                        table._update_by_id(src_id, {rel_field: None}, _propagate=True, _guard=set())
                    except Exception:
                        pass

        with self.db._transaction():
            self.db.cursor.execute(f"DELETE FROM {self.name} WHERE {id_col} = ?", (id_value,))

    def delete_one(self, obj: ModelT) -> None:
        id_col = "_id" if "_id" in self._field_types else "id"
        id_value = getattr(obj, id_col, None)
        if id_value is None:
            raise SillyDbError(f"Object {obj} does not have an '{id_col}' field for deletion")
        self.delete_by_id(id_value)

    def delete_first(self) -> None:
        first_obj = self.get_first()
        if first_obj is not None:
            self.delete_one(first_obj)

    def delete_filter(self, filters: list[str] | None =None) -> None:
        if filters is None or len(filters) == 0:
            self.delete_all()
            return
        where_sql = " AND ".join(filters)
        with self.db._transaction():
            self.db.cursor.execute(f"DELETE FROM {self.name} WHERE {where_sql}")

    def count(self) -> int:
        with self.db._transaction():
            self.db.cursor.execute(f"SELECT COUNT(*) FROM {self.name}")
            return self.db.cursor.fetchone()[0]

    def register(self, data: dict | Any) -> None:
        """Create a new entry in this table."""
        if self.singleton and self.count() >= 1:
            raise SillyDbError(f"Table '{self.name}' is a singleton and already has an entry")
        # prepare values, serializing lists/dicts to JSON and converting bools to ints
        if is_dataclass(data) and not isinstance(data, type):
            # preserve raw dataclass attribute values (avoid nested asdict conversion of relation objects)
            data = {k: getattr(data, k) for k in data.__dataclass_fields__.keys()}
        assert isinstance(data, dict), "data must be a dict at this point"
        # skip Mtm fields when building INSERT columns (they are stored in join tables)
        insert_keys = [k for k in data.keys() if not (k in self._relations and isinstance(self._relations.get(k), Mtm))]
        columns = ", ".join(insert_keys)
        placeholders = ", ".join("?" for _ in insert_keys)
        values_list = []
        for k in insert_keys:
            v = data[k]
            ftype = self._field_types.get(k)
            origin = get_origin(ftype) if ftype is not None else None
            # If the value is the relation descriptor (e.g. Oto instance as default), store NULL
            if isinstance(v, SillyOrmRelation):
                values_list.append(None)
                continue
            # If value is a dataclass instance or has an _id, store its id for relation fields
            if not (v is None) and not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                values_list.append(getattr(v, "_id"))
                continue
            if v is None:
                values_list.append(None)
            elif ftype == bool:
                values_list.append(1 if v else 0)
            elif ftype == int or ftype == float or ftype == str:
                values_list.append(v)
            elif ftype == dict or origin == dict or ftype == list or origin == list:
                values_list.append(json.dumps(v))
            else:
                # fallback: try JSON serialization, otherwise store as str
                try:
                    values_list.append(json.dumps(v))
                except Exception:
                    values_list.append(str(v))
        values = tuple(values_list)
        with self.db._transaction():
            if columns:
                self.db.cursor.execute(
                    f"INSERT INTO {self.name} ({columns}) VALUES ({placeholders})", values
                )
            else:
                # no columns to insert (all fields are Mtm or defaults), insert default row
                self.db.cursor.execute(f"INSERT INTO {self.name} DEFAULT VALUES")
            # determine source id (_id provided or lastrowid for autoincrement)
            if "_id" in self._field_types and "_id" in data:
                source_id = data.get("_id")
            else:
                source_id = self.db.cursor.lastrowid
            # propagate Oto relations for provided relation fields
            guard: set = set()
            # handle relation fields: Oto/Mto handled via propagation, Mtm handled via join table sync
            for k, rel in self._relations.items():
                if k not in data:
                    continue
                v = data[k]
                if v is None or isinstance(v, SillyOrmRelation):
                    continue
                if isinstance(rel, Mtm):
                    # normalize to list of ids
                    if v is None:
                        new_list = []
                    elif isinstance(v, list):
                        new_list = [getattr(item, "_id", item) if (not isinstance(item, (str, int)) and hasattr(item, "_id")) else item for item in v]
                    else:
                        # single value
                        if is_dataclass(v) and not isinstance(v, type):
                            new_list = [getattr(v, "_id", None) or getattr(v, "id", None)]
                        elif not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                            new_list = [getattr(v, "_id")]
                        else:
                            new_list = [v]
                    try:
                        self._sync_mtm_join(source_id, k, new_list, [])
                    except Exception:
                        pass
                    continue
                # single-target relations
                # resolve id from object or value
                if is_dataclass(v) and not isinstance(v, type):
                    vid = getattr(v, "_id", None) or getattr(v, "id", None)
                elif not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                    vid = getattr(v, "_id")
                else:
                    vid = v
                if vid is None:
                    continue
                try:
                    if isinstance(rel, Mto):
                        self._propagate_mto(source_id, k, vid, old_target_id=None, _guard=guard)
                    else:
                        # Oto or other single-target relations
                        self._propagate_oto(source_id, k, vid, old_target_id=None, _guard=guard)
                except Exception:
                    pass

    def get_all(self) -> list[ModelT]:
        return self._rows_to_models(self._get_raw("1"))

    def get_all_paginate(self, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[list[ModelT], int, int, int]:
        rows, page, page_size, count = self._get_raw_paginated("1", page, page_size)
        return self._rows_to_models(rows), page, page_size, count

    def get_by_id(self, id_value: Any, recursive_level: int | None = None) -> ModelT | None:
        if recursive_level is None:
            recursive_level = self.db.recursive_level
        id_col = "_id" if "_id" in self._field_types else "id"
        with self.db._transaction():
            self.db.cursor.execute(f"SELECT * FROM {self.name} WHERE {id_col} = ?", (id_value,))
            row = self.db.cursor.fetchone()
        if row is None:
            return None
        return self._rows_to_models([row], recursive_level=recursive_level)[0]

    def get_first(self, recursive_level: int | None = None) -> ModelT | None:
        if recursive_level is None:
            recursive_level = self.db.recursive_level
        with self.db._transaction():
            self.db.cursor.execute(f"SELECT * FROM {self.name} LIMIT 1")
            row = self.db.cursor.fetchone()
        if row is None:
            return None
        return self._rows_to_models([row], recursive_level=recursive_level)[0]

    def get_filter(self, filters: list[str] | None =None) -> list[ModelT]:
        if filters is None or len(filters) == 0:
            return self.get_all()
        where_sql = " AND ".join(filters)
        query = f"SELECT * FROM {self.name} WHERE {where_sql}"
        with self.db._transaction():
            self.db.cursor.execute(query)
            rows = self.db.cursor.fetchall()
        return self._rows_to_models(rows)

    def get_filter_paginate(self, filters: list[str] | None =None, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Tuple[list[ModelT], int, int, int]:
        if filters is None or len(filters) == 0:
            return self.get_all_paginate(page, page_size)
        where_sql = " AND ".join(filters)
        query = f"SELECT * FROM {self.name} WHERE {where_sql}"
        rows, page, page_size, count = self._get_raw_paginated(where_sql, page, page_size)
        return self._rows_to_models(rows), page, page_size, count

    def _update_by_id(self, id_value: Any, data: dict | Any, _propagate: bool = True, _guard: set | None = None) -> None:
        if is_dataclass(data) and not isinstance(data, type):
            # preserve raw dataclass attribute values to correctly handle relation objects
            data = {k: getattr(data, k) for k in data.__dataclass_fields__.keys()}
        assert isinstance(data, dict), "data must be a dict at this point"
        set_clauses = []
        values_list = []
        # collect old relation values for propagation
        old_relation_values: dict[str, Any] = {}
        relation_fields_changed: list[str] = []
        for k in data.keys():
            if k in self._relations:
                # fetch current value; Mtm stored in join table
                rel = self._relations.get(k)
                if isinstance(rel, Mtm):
                    target = getattr(rel, 'target', None) if getattr(rel, 'target', None) is not None else (rel.targets[0] if getattr(rel, 'targets', None) else None)
                    if target is None:
                        old_relation_values[k] = None
                    else:
                        join_name = self._find_mtm_join_name(k, target)
                        try:
                            sname, tname = sorted([self.name, target])
                            with self.db._transaction():
                                if sname == self.name:
                                    self.db.cursor.execute(f"SELECT tgt_id FROM {join_name} WHERE src_id = ?", (id_value,))
                                else:
                                    self.db.cursor.execute(f"SELECT src_id FROM {join_name} WHERE tgt_id = ?", (id_value,))
                                rows = self.db.cursor.fetchall()
                            old_relation_values[k] = [r[0] for r in rows]
                        except Exception:
                            old_relation_values[k] = []
                else:
                    # fetch current value from column
                    id_col = "_id" if "_id" in self._field_types else "id"
                    with self.db._transaction():
                        self.db.cursor.execute(f"SELECT {k} FROM {self.name} WHERE {id_col} = ?", (id_value,))
                        row = self.db.cursor.fetchone()
                    if row is None:
                        old_relation_values[k] = None
                    else:
                        raw = row[0]
                        if isinstance(rel, Otm):
                            if raw is None:
                                old_relation_values[k] = None
                            else:
                                try:
                                    old_relation_values[k] = json.loads(raw)
                                except Exception:
                                    # fallback: if stored as plain text, treat as single-item list
                                    old_relation_values[k] = [raw]
                        else:
                            old_relation_values[k] = raw
                relation_fields_changed.append(k)
        for k in data.keys():
            v = data[k]
            ftype = self._field_types.get(k)
            origin = get_origin(ftype) if ftype is not None else None
            # skip Mtm fields from the UPDATE statement (they are stored in join tables)
            if k in self._relations and isinstance(self._relations.get(k), Mtm):
                # still process propagation later
                continue
            # If value is a dataclass instance or has an _id, store its id
            if is_dataclass(v) and not isinstance(v, type):
                vid = getattr(v, "_id", None) or getattr(v, "id", None)
                values_list.append(vid)
                set_clauses.append(f"{k} = ?")
                continue
            if not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                values_list.append(getattr(v, "_id"))
                set_clauses.append(f"{k} = ?")
                continue

            if v is None:
                values_list.append(None)
            elif ftype == bool:
                values_list.append(1 if v else 0)
            elif ftype == int or ftype == float or ftype == str:
                values_list.append(v)
            elif ftype == dict or origin == dict or ftype == list or origin == list:
                values_list.append(json.dumps(v))
            else:
                # fallback: try JSON serialization, otherwise store as str
                try:
                    values_list.append(json.dumps(v))
                except Exception:
                    values_list.append(str(v))
            set_clauses.append(f"{k} = ?")
        set_sql = ", ".join(set_clauses)
        id_col = "_id" if "_id" in self._field_types else "id"
        query = f"UPDATE {self.name} SET {set_sql} WHERE {id_col} = ?"
        with self.db._transaction():
            # If there are no non-Mtm columns to update, skip the UPDATE statement
            if set_sql.strip():
                self.db.cursor.execute(query, (*values_list, id_value))
            # after update, propagate relation changes if requested
            if _propagate and relation_fields_changed:
                if _guard is None:
                    _guard = set()
                for k in relation_fields_changed:
                    # determine new value
                        rel = self._relations.get(k)
                        new_val = None
                        if k in data:
                            v = data[k]
                            # handle Otm lists
                            if isinstance(rel, Otm):
                                if v is None:
                                    new_val = None
                                else:
                                    # expect list-like
                                    if isinstance(v, str):
                                        try:
                                            new_val = json.loads(v)
                                        except Exception:
                                            new_val = [v]
                                    elif isinstance(v, list):
                                        parsed = []
                                        for item in v:
                                            if is_dataclass(item) and not isinstance(item, type):
                                                parsed.append(getattr(item, "_id", None) or getattr(item, "id", None))
                                            elif not isinstance(item, (str, int, float, bool, dict, list)) and hasattr(item, "_id"):
                                                parsed.append(getattr(item, "_id"))
                                            else:
                                                parsed.append(item)
                                        new_val = parsed
                                    else:
                                        # single value, wrap
                                        if is_dataclass(v) and not isinstance(v, type):
                                            new_val = [getattr(v, "_id", None) or getattr(v, "id", None)]
                                        elif not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                                            new_val = [getattr(v, "_id")]
                                        else:
                                            new_val = [v]
                            else:
                                # single-target relation (Oto/Mto) or scalar
                                if is_dataclass(v) and not isinstance(v, type):
                                    new_val = getattr(v, "_id", None) or getattr(v, "id", None)
                                elif not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                                    new_val = getattr(v, "_id")
                                else:
                                    new_val = v
                            # normalize Mtm lists to ids
                            if isinstance(rel, Mtm):
                                if new_val is None:
                                    new_val = []
                                elif isinstance(new_val, list):
                                    parsed = []
                                    for item in new_val:
                                        if is_dataclass(item) and not isinstance(item, type):
                                            parsed.append(getattr(item, "_id", None) or getattr(item, "id", None))
                                        elif not isinstance(item, (str, int, float, bool, dict, list)) and hasattr(item, "_id"):
                                            parsed.append(getattr(item, "_id"))
                                        else:
                                            parsed.append(item)
                                    new_val = parsed
                                else:
                                    # single value
                                    if is_dataclass(new_val) and not isinstance(new_val, type):
                                        new_val = [getattr(new_val, "_id", None) or getattr(new_val, "id", None)]
                                    elif not isinstance(new_val, (str, int, float, bool, dict, list)) and hasattr(new_val, "_id"):
                                        new_val = [getattr(new_val, "_id")]
                                    else:
                                        new_val = [new_val]
                        old_val = old_relation_values.get(k)
                        try:
                                if isinstance(rel, Mto):
                                    self._propagate_mto(id_value, k, new_val, old_target_id=old_val, _guard=_guard)
                                elif isinstance(rel, Mtm):
                                    # new_val/old_val are lists of ids
                                    try:
                                        self._sync_mtm_join(id_value, k, new_val or [], old_val or [])
                                    except Exception:
                                        pass
                                elif isinstance(rel, Otm):
                                    # old_val/new_val are lists or None
                                    self._propagate_otm_on_change(id_value, k, new_val, old_val, _guard=_guard)
                                else:
                                    self._propagate_oto(id_value, k, new_val, old_target_id=old_val, _guard=_guard)
                        except Exception:
                            pass

    def update_one(self, obj: ModelT) -> None:
        id_col = "_id" if "_id" in self._field_types else "id"
        id_value = getattr(obj, id_col, None)
        if id_value is None:
            raise SillyDbError(f"Object {obj} does not have an '{id_col}' field for update")
        self._update_by_id(id_value, obj)

    def save(self, obj: ModelT) -> None:
        id_col = "_id" if "_id" in self._field_types else "id"
        id_value = getattr(obj, id_col, None)
        if self.get_by_id(id_value) is not None:
            self.update_one(obj)
        else:
            self.register(obj)


    def update_filter(self, filters: list[str] | None, data: dict | Any) -> None:
        if is_dataclass(data) and not isinstance(data, type):
            data = asdict(data)
        assert isinstance(data, dict), "data must be a dict at this point"
        if not data:
            return

        # Don't allow updating the text primary key field
        data.pop("_id", None)

        # Do not allow bulk updates to relation fields (Oto) — require update_one/update_by_id
        for k in data.keys():
            if k in self._relations:
                raise SillyDbError("Bulk update of relation fields (Oto) is not allowed; use update_one/update_by_id")

        set_clauses = []
        values = []
        for k, v in data.items():
            ftype = self._field_types.get(k)
            origin = get_origin(ftype) if ftype is not None else None
            # If value is a dataclass instance or has an _id, store its id
            if is_dataclass(v) and not isinstance(v, type):
                vid = getattr(v, "_id", None) or getattr(v, "id", None)
                values.append(vid)
                set_clauses.append(f"{k} = ?")
                continue
            if not isinstance(v, (str, int, float, bool, dict, list)) and hasattr(v, "_id"):
                values.append(getattr(v, "_id"))
                set_clauses.append(f"{k} = ?")
                continue
            if v is None:
                values.append(None)
            elif ftype == bool:
                values.append(1 if v else 0)
            elif ftype in (int, float, str):
                values.append(v)
            elif ftype == dict or origin == dict or ftype == list or origin == list:
                values.append(json.dumps(v))
            else:
                try:
                    values.append(json.dumps(v))
                except Exception:
                    values.append(str(v))
            set_clauses.append(f"{k} = ?")

        set_sql = ", ".join(set_clauses)

        if filters is None or len(filters) == 0:
            query = f"UPDATE {self.name} SET {set_sql}"
            params = tuple(values)
        else:
            where_sql = " AND ".join(filters)
            query = f"UPDATE {self.name} SET {set_sql} WHERE {where_sql}"
            params = tuple(values)

        with self.db._transaction():
            self.db.cursor.execute(query, params)