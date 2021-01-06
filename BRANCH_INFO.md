#  BRANCH INFO
this branch tries to use a distributed fault tolerant sqlite db backend to achieve HA and data safety/redundancy

## ressources:
  - https://github.com/rqlite/rqlite
  - https://docs.djangoproject.com/en/3.1/ref/databases/#subclassing-the-built-in-database-backends
  - https://github.com/canonical/dqlite # seems not that prominent in respect to rqlite

there are also various other ressources such as python clients and sqlAlchemy packages in: https://github.com/rqlite




django sqlAlchemy ORM client https://github.com/aldjemy/aldjemy (maybe usefully in combination with the rqlite sqlAlchemy bindings but not sure)
