# Changelog

## [1.2.8]

- Rename *.yml to *.yaml

## [1.2.7]

- Remove use_conditional and make it always to use

## [1.2.6]

- Add list[dict] type to params in updates for executemany support

## [1.2.5]

- Minimize differences across all *-client source code

## [1.2.4]

- Support nested #foreach

## [1.2.3]

- Support #foreach dynamic loop directive

## [1.2.2]

- Support ${param} template variable and enforce ${param} in #if conditions

## [1.2.1]

- Collect queries in Client class and delete query_all.py

## [1.2.0]

- Support name referencing via `#include name` and `#include name(key)`

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
