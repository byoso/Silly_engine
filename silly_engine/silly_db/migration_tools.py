
from __future__ import annotations
from typing import Iterable

from .silly_db import SillyDb


def _refresh_table_metadata(db: SillyDb, table: str) -> None:
	"""Update the in-memory Table._field_types to reflect current DB schema.

	This avoids re-instantiating Table (which would re-create missing columns
	based on the dataclass model) and prevents dropped columns from being
	re-added.
	"""
	if table not in db.tables:
		return
	tbl = db.tables[table]
	try:
		info = _read_table_info(db, table)
		new_field_types: dict[str, type] = {}
		for row in info:
			name = row[1]
			sqltype = (row[2] or "").upper()
			if sqltype.startswith("INT"):
				new_field_types[name] = int
			elif sqltype.startswith("REAL"):
				new_field_types[name] = float
			elif sqltype.startswith("TEXT") or sqltype == "":
				new_field_types[name] = str
			else:
				new_field_types[name] = str
		tbl._field_types = new_field_types
	except Exception:
		# best-effort; do not raise
		pass


def _read_table_info(db: SillyDb, table: str) -> list[tuple]:
	with db._transaction():
		db.cursor.execute(f"PRAGMA table_info({_quote_ident(table)})")
		return db.cursor.fetchall()


def _build_columns_from_info(info_rows: Iterable[tuple], rename_map: dict[str, str] | None = None, drop: set | None = None) -> list[str]:
	cols: list[str] = []
	for row in info_rows:
		# PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
		name = row[1]
		typ = row[2] or ""
		notnull = bool(row[3])
		default = row[4]
		pk = bool(row[5])
		if drop and name in drop:
			continue
		out_name = rename_map.get(name, name) if rename_map else name
		parts = [ _quote_ident(out_name), typ if typ else ""
		]
		if pk:
			parts.append("PRIMARY KEY")
		if notnull:
			parts.append("NOT NULL")
		if default is not None:
			parts.append(f"DEFAULT {default}")
		cols.append(" ".join([p for p in parts if p]))
	return cols


def _copy_data_sql(old_cols: list[str], new_cols: list[str], rename_map: dict[str, str] | None = None) -> str:
	# generate SELECT clause mapping old column names to new names when needed
	select_parts: list[str] = []
	for nc in new_cols:
		# new column identifier (may be quoted)
		# find the corresponding old column name
		if rename_map:
			inv = {v: k for k, v in rename_map.items()}
			bare_new = nc.strip('"')
			old = inv.get(bare_new, bare_new)
		else:
			old = nc.strip('"')
		select_parts.append(f"{_quote_ident(old)}")
	return ", ".join(select_parts)

def _quote_ident(name: str) -> str:
	# Avoid backslashes inside f-string expressions; use concatenation instead.
	return '"' + name.replace('"', '""') + '"'

def rename_table(db: SillyDb, old: str, new: str) -> None:
	"""Rename a table safely using SQLite's ALTER TABLE when possible.

	This updates the in-memory `db.tables` mapping if the table was registered.
	"""
	# If the target table already exists, copy overlapping columns then drop the old table
	try:
		new_info = _read_table_info(db, new)
	except Exception:
		new_info = []
	if new_info:
		# copy common columns from old to new inside a transaction
		old_info = _read_table_info(db, old)
		old_cols = [r[1] for r in old_info]
		new_cols = [r[1] for r in new_info]
		common = [c for c in old_cols if c in new_cols]
		if common:
			cols_list = ", ".join([_quote_ident(c) for c in common])
			with db._transaction():
				db.cursor.execute(f"INSERT INTO {_quote_ident(new)} ({cols_list}) SELECT {cols_list} FROM {_quote_ident(old)}")
		# drop old table and update registry
		with db._transaction():
			db.cursor.execute(f"DROP TABLE {_quote_ident(old)}")
		if old in db.tables:
			del db.tables[old]
		# refresh metadata for destination
		_refresh_table_metadata(db, new)
		return

	# otherwise perform a direct rename
	with db._transaction():
		db.cursor.execute(f'ALTER TABLE {_quote_ident(old)} RENAME TO {_quote_ident(new)}')
	# update registry mapping if present
	if old in db.tables:
		tbl = db.tables.pop(old)
		tbl.name = new
		db.tables[new] = tbl


def rename_field(db: SillyDb, table: str, old_field: str, new_field: str) -> None:
	"""Rename a column by recreating the table with the renamed column.

	This is the portable approach for SQLite versions that lack direct column rename.
	Indexes and triggers are not preserved; use carefully.
	"""
	info = _read_table_info(db, table)
	if not info:
		raise ValueError(f"Table '{table}' does not exist")
	cols = [r[1] for r in info]
	# if old field doesn't exist, nothing to do
	if old_field not in cols:
		return
	# if new field already exists, simply copy values then drop the old field
	if new_field in cols:
		try:
			with db._transaction():
				# copy values from old to new when new is NULL
				db.cursor.execute(
					f"UPDATE {_quote_ident(table)} SET {_quote_ident(new_field)} = {_quote_ident(old_field)} WHERE {_quote_ident(new_field)} IS NULL"
				)
		except Exception:
			# if copy fails, raise to signal migration failure
			raise
		# now drop the old field
		remove_field(db, table, old_field)
		return

	rename_map = {old_field: new_field}
	new_cols = _build_columns_from_info(info, rename_map=rename_map)
	old_col_names = [r[1] for r in info]

	tmp = f"{table}__tmp_mig"
	with db._transaction():
		# create tmp table
		db.cursor.execute(f"CREATE TABLE {_quote_ident(tmp)} ({', '.join(new_cols)})")
		# copy data
		new_col_idents = [c.split()[0] for c in new_cols]
		copy_sql = _copy_data_sql(old_col_names, new_col_idents, rename_map=rename_map)
		db.cursor.execute(f"INSERT INTO {_quote_ident(tmp)} ({', '.join(new_col_idents)}) SELECT {copy_sql} FROM {_quote_ident(table)}")
		# drop old, rename tmp
		db.cursor.execute(f"DROP TABLE {_quote_ident(table)}")
		db.cursor.execute(f"ALTER TABLE {_quote_ident(tmp)} RENAME TO {_quote_ident(table)}")
	# refresh in-memory Table metadata so it mirrors DB without re-instantiating
	_refresh_table_metadata(db, table)


def remove_field(db: SillyDb, table: str, field: str) -> None:
	"""Remove a column by recreating the table without that column.

	Indexes and triggers are not preserved; use with backups.
	"""
	info = _read_table_info(db, table)
	if not info:
		raise ValueError(f"Table '{table}' does not exist")
	drop = {field}
	new_cols = _build_columns_from_info(info, drop=drop)
	old_col_names = [r[1] for r in info if r[1] not in drop]

	tmp = f"{table}__tmp_mig"
	with db._transaction():
		db.cursor.execute(f"CREATE TABLE {_quote_ident(tmp)} ({', '.join(new_cols)})")
		new_col_idents = [c.split()[0] for c in new_cols]
		copy_sql = ", ".join([_quote_ident(n) for n in old_col_names])
		db.cursor.execute(f"INSERT INTO {_quote_ident(tmp)} ({', '.join(new_col_idents)}) SELECT {copy_sql} FROM {_quote_ident(table)}")
		db.cursor.execute(f"DROP TABLE {_quote_ident(table)}")
		db.cursor.execute(f"ALTER TABLE {_quote_ident(tmp)} RENAME TO {_quote_ident(table)}")
	# refresh in-memory Table metadata so it mirrors DB without re-instantiating
	_refresh_table_metadata(db, table)
