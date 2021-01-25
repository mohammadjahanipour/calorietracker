#  BRANCH INFO
this branch tries to use a distributed fault tolerant sqlite db backend to achieve HA and data safety/redundancy

## ressources:
  - https://github.com/rqlite/rqlite
  - https://docs.djangoproject.com/en/3.1/ref/databases/#subclassing-the-built-in-database-backends
  - https://github.com/canonical/dqlite # seems not that prominent in respect to rqlite

there are also various other ressources such as python clients and sqlAlchemy packages in: https://github.com/rqlite




django sqlAlchemy ORM client https://github.com/aldjemy/aldjemy (maybe usefully in combination with the rqlite sqlAlchemy bindings but not sure)


------------


rqlite with django-rqlite fails because of:
django.db.utils.Error: {"error": "no such function: JSON"}
sqlite3.Error: {"error": "no such function: JSON"}

my best guess atm is this is because:

    "
    Missing Functionality
    Django has a huge number of functions added on top of plain SQLite, to provide advanced manipulations have a look here, these function cannot be used anymore as they are no longer available in go.

    For more information: https://github.com/rqlite/rqlite/pull/523
    "
