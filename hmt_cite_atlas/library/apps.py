from django.apps import AppConfig as BaseAppConfig
from django.db.backends.signals import connection_created


class LibraryConfig(BaseAppConfig):
    name = "library"


def tweak_sqlite_pragma(sender, connection, **kwargs):
    """
    Customize PRAGMA settings for SQLite
    """
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA synchronous=OFF;")
        cursor.execute("PRAGMA cache_size=100000;")
        cursor.execute("PRAGMA journal_mode=MEMORY;")


connection_created.connect(tweak_sqlite_pragma)
