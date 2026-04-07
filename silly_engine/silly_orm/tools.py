
class SillyDbError(Exception):
    pass


def _is_migration_applicable(db_version: str, migration_version: str) -> bool:
    """
    Return True if the migration is more recent than the current db version.
    """
    version_db = [int(n) for n in db_version.split(".")]
    version_migration = [int(n) for n in migration_version.split(".")]
    return version_db < version_migration


# =======================================================================
# Migration helpers
# =======================================================================

def raw_sql_migration(db, sql: str):
    db.connector.execute(sql)