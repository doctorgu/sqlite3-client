# Changelog

## [1.1.1]

- Refactoring code to apply ruff format, ruff check

## [1.1.0]

- Query changed to yml file format from python dict format.

## [1.0.2]

RealDictRow to sqlite3.Row

## [1.0.1]

Support executemany() for insert / update when params is list of dict

## [1.0.0]

Initial release:

- Sqlite3 helper function to run SQLite query with #if support
- Connection pooling with minconn / maxconn
- Bilingual column alias support
- Transaction management with context manager
- Streaming CSV export support
