# Sqlite3Client — Modern SQLite Helper for Python

A lightweight, opinionated wrapper around **sqlite3** with built-in support for:

- Connection pooling (`minconn` / `maxconn`)
- Query dictionary management
- Conditional SQL (`#if` / `#elif` / `#endif`)
- Dynamic Loop (`#foreach` / `#endfor` / `#endforeach`)
- Include Query Snippet (`#include`)
- Template Variable (`${param}`)
- Bilingual column aliases (`en|ko`)
- Simple transaction handling via context manager
- Safe parameter binding (`:param` syntax)
- Streaming CSV export support

> Successor-friendly alternative to raw sqlite3 with better developer experience.

## Installation

```bash
pip install sqlite3-client
```

> Note: `sqlite3-client` is a custom helper class. See full source in repository.

## Quick Start

### 1. Define Queries

```python
qry_dic: dict[str, str] = {}

qry_dic.update(
    {
        "read_user_id_all": """
SELECT  user_id
FROM    t_user
"""
    }
)

qry_dic.update(
    {
        "upsert_user": """
INSERT INTO t_user
    (
        user_id, user_name, user_rank
    )
VALUES
    (
        :user_id, :user_name, :user_rank
    )
ON CONFLICT (user_id)
DO UPDATE
SET     user_name = :user_name,
        user_rank = :user_rank,
        update_time = CURRENT_TIMESTAMP
RETURNING user_name, user_rank;
"""
    }
)
```

### 2. Configure Database Connection

```python
from sqlite3_client.settings import Settings

db_settings = Settings(
    database="test.db",
    minconn=3,
    maxconn=10,
    connect_timeout=5,
    use_en_ko_column_alias=True,
    use_conditional=True,
    all_query=qry_dic,
    before_read_execute=lambda qry_key, params, qry_str, qry_with_value: print(
        f'READ_ROWS_START, QRY_KEY: "{qry_key}", QRY_WITH_VALUE: {qry_with_value}'
    ),
    after_read_execute=lambda qry_key, duration: print(
        f'READ_ROWS_END, QRY_KEY: "{qry_key}", DURATION: {duration}'
    ),
    before_update_execute=lambda qry_key, params, params_out, qry_str, qry_with_value: (
        print(f'UPDATES_START, QRY_KEY: "{qry_key}", QRY_WITH_VALUE: {qry_with_value}')
    ),
    after_update_execute=lambda qry_key, row_count, params_out, duration: print(
        f'UPDATES_END, QRY_KEY: "{qry_key}", DURATION: {duration}'
    ),
)
```

### 3. Basic Usage

```python
from sqlite3_client.client import Client

db = Client(db_settings=db_settings)

# Read single row
row = db.read_row("read_user_id_all", {})
print(row)  # {'user_id': 'gildong.hong'}

# Read all rows
rows = db.read_rows("read_user_id_all", {})
print(rows[:2])
```

## Create / Update / Delete Operations

### `update()` — Single CUD Statement

Returns affected row count:

```python
affected = db.update(
    "upsert_user", {"user_id": "gildong.hong", "user_name": "홍길동", "user_rank": 1}
)
print("Affected rows:", affected)  # 1
```

### Capture Output Parameters

```python
params_out = {"user_name": "", "user_rank": 0}
db.update(
    "upsert_user",
    {"user_id": "gildong.hong", "user_name": "홍길동", "user_rank": 1},
    params_out=params_out,
)
print("Returned name:", params_out["user_name"], params_out["user_rank"])  # 홍길동 1
```

### `updates()` — Batch Execution

```python
batch = [
    ("upsert_user", {"user_id": "sunja.kim", "user_name": "김순자", "user_rank": 2}),
    ("upsert_user", {"user_id": "malja.kim", "user_name": "김말자", "user_rank": 3}),
]

results = db.updates(batch)
print("Batch results:", results)  # [1, 1]
```

## Transaction Support with `with`

Automatically commits on success, rolls back on exception:

```python
with Client(db_settings=db_settings) as db:
    new_id = "youngja.lee"
    db.update("upsert_user", {"user_id": new_id, "user_name": "이영자", "user_rank": 4})
    db.update("delete_user", {"user_id": new_id})  # Oops! Will rollback entire block
    print("This won't print if error occurs")
```

## Partially return CSV

Read rows partially and return immediately to client to show progress in client:

```python
# Flask
@app.route("/read-csv-partial")
def read_csv_partial():
    """read csv partial"""

    db_client = Client(db_settings=db_settings)
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    return Response(
        db_client.read_csv_partial("read_csv_partial", {}),
        mimetype="text/csv",
        headers={
            # if FE and BE are on different origins,
            # server must expose the Content-Disposition header
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f'attachment; filename="{filename}"',
            # Very important for progressive saving in many browsers
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # Important if using nginx
            "Transfer-Encoding": "chunked",
        },
    )


# Fast API
@router.get("/read-csv-partial-async")
async def read_csv_partial_async():
    """read csv partial async"""

    db_client = Client(db_settings=db_settings)
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    return StreamingResponse(
        content=db_client.read_csv_partial_async("read_csv_partial", {}),
        media_type="text/csv",
        headers={
            # if FE and BE are on different origins,
            # server must expose the Content-Disposition header
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": f'attachment; filename="{filename}"',
            # Very important for progressive saving in many browsers
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # Important if using nginx
            "Transfer-Encoding": "chunked",
        },
    )
```

## Bilingual Column Aliases (English ↔ Korean)

Enabled when `use_en_ko_column_alias=True` and `en` not omitted:

```python
qry_dic.update(
    {
        "read_user_alias": """
SELECT  user_id "Id|아이디", user_name "Name|이름", user_rank "Rank|순위"
FROM    t_user
WHERE   user_id = :user_id
"""
    }
)
```

### English mode (`en=True`)

```python
rows = db.read_rows("read_user_alias", {"user_id": "gildong.hong"}, en=True)
print(rows[0])
# {'Id': 'gildong.hong', 'Name': '홍길동'}
```

### Korean mode (`en=False`)

```python
rows = db.read_rows("read_user_alias", {"user_id": "gildong.hong"}, en=False)
print(rows[0])
# {'아이디': 'gildong.hong', '이름': '홍길동'}
```

## Conditional SQL (`#if`, `#elif`, `#endif`)

Enabled when `use_conditional=True`:

```python
qry_dic.update(
    {
        "read_user_search": """
SELECT  user_id, user_name, user_rank, insert_time, update_time
FROM    t_user
WHERE   1 = 1
#if ${user_id}
        AND user_id = :user_id
#elif ${user_name}
        AND user_name LIKE :user_name
#elif ${user_rank}
        AND user_rank <= :user_rank
#endif
"""
    }
)
```

### Example: Search by `user_id`

```python
rows = db.read_rows(
    "read_user_search", {"user_id": "gildong.hong", "user_name": "", "user_rank": 0}
)
print([r["user_name"] for r in rows])
# ['홍길동']
```

### Example: Search by `user_name` (partial match)

```python
rows = db.read_rows(
    "read_user_search", {"user_id": "", "user_name": "%김%", "user_rank": 0}
)
print([r["user_name"] for r in rows])
# ['김순자', '김말자']
```

### Example: Search by `user_rank` (partial match)

```python
rows = db.read_rows(
    "read_user_search", {"user_id": "", "user_name": "", "user_rank": 3}
)
print([r["user_name"] for r in rows])
# ['홍길동', '김순자', '김말자']
```

## Include Query Snippet (`#include`)

Include reusable query fragments or sub-queries. Line-based only (no inline `#include`), and can be used inside `#if` blocks.

- `#include name`: When the target query's `value` is a string (no sub-keys).
- `#include name(key)`: When the target query's `value` is a dictionary (parent of sub-keys).

```yaml
- name: _filter_by_key
  value:
    user_id: "            AND user_id = :user_id"
    user_name: "            AND user_name LIKE :user_name"
    user_rank: "            AND user_rank <= :user_rank"

- name: read_user_by_key
  value: |
    SELECT  user_id
    FROM    t_user
    WHERE   1 = 1
    #if ${user_id}
    #include _filter_by_key(user_id)
    #elif ${user_name}
    #include _filter_by_key(user_name)
    #elif ${user_rank}
    #include _filter_by_key(user_rank)
    #endif
```

If a parameter is passed and no matching sub-key exists, an error is raised.

## Template Variable (`${param}`)

Support MyBatis-style template variable substitution (e.g. dynamic table names, column names). Substituted directly into the SQL text before execution:

```yaml
- name: delete_data_by_version
  value: |
    DELETE
    FROM    ${table}
    WHERE   version = :version
```

```python
db.update("delete_data_by_version", {"table": "data_menu", "version": "1.0.0"})
```

If a referenced `${param}` does not exist in `params`, a `KeyError` is raised. If its value is `None`, a `ValueError` is raised.

## Dynamic Loop (`#foreach`)

Support dynamic collection iteration mimicking MyBatis `<foreach>`. It safely binds dynamic parameter keys in `params` (e.g. `:__f_item_0_0`) preventing SQL injection, and seamlessly replaces them with values during logging.

### Supported Syntax

- **Item iteration**: `#foreach item in ${user_ids} open="(" separator="," close=")"`
- **With index**: `#foreach idx, item in ${items} separator=","`
- **Closing tag**: `#endfor` or `#endforeach`

### Inside `#foreach` Body

- `#{item}` or `:item`: Parameterized bind variable (mapped to `:__f_...` in SQLite).
- `#{item.prop}` or `:item.prop`: Property access for lists of dictionaries/objects.
- `${item}`, `${item.prop}`, `${index}`: Direct template string substitution.

### Example 1: IN Clause

```yaml
- name: read_users_in
  value: |
    SELECT  user_id, user_name
    FROM    t_user
    WHERE   user_id IN
    #foreach item in ${user_ids} open="(" separator=", " close=")"
        #{item}
    #endfor
```

```python
rows = db.read_rows("read_users_in", {"user_ids": ["gildong.hong", "sunja.kim"]})
```

Generated query sent to SQLite:
```sql
SELECT  user_id, user_name
FROM    t_user
WHERE   user_id IN
('gildong.hong', 'sunja.kim')
```

### Example 2: Multi-row INSERT (Batch Insert)

> [!NOTE]
> Native `executemany` with list or tuple of parameter is faster.

```yaml
- name: insert_users
  value: |
    INSERT INTO t_user (user_id, user_name, user_rank) VALUES
    #foreach user in ${users} separator=","
        (#{user.id}, #{user.name}, #{user.rank})
    #endfor;
```

```python
db.update(
    "insert_users",
    {
        "users": [
            {"id": "user1", "name": "Alice", "rank": 1},
            {"id": "user2", "name": "Bob", "rank": 2},
        ]
    },
)
```

### Example 3: Combined with `#if`

```yaml
- name: read_users_filtered
  value: |
    SELECT  user_id, user_name
    FROM    t_user
    WHERE   1 = 1
    #if ${user_ids}
        AND user_id IN
        #foreach id in ${user_ids} open="(" separator="," close=")"
            #{id}
        #endfor
    #endif
```

If `user_ids` is not provided or empty, the entire block is omitted without raising errors. If the collection is empty (`[]`), `#foreach` produces an empty string without stray parentheses.

## Logging support

- `before_read_execute` called before execute query for read
- `after_read_execute` called after execute query for read
- `before_update_execute` called before execute query for CUD
- `after_update_execute` called after execute query for CUD

Can be replaced `print` with `logger`:

### Example: Use logger to write debug info

```python
import logging


def get_sql_logger(name="sql"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            filename="sql.log",
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)7s] %(message)s",
            encoding="utf-8",
        )
    return logger


logger = get_sql_logger()
db_settings.before_read_execute = lambda qry_key, params, qry_str, qry_with_value: (
    logger.debug(
        f'READ_ROWS_START, QRY_KEY: "{qry_key}", QRY_WITH_VALUE: {qry_with_value}'
    )
)
```

## Safety & Security

### Q: Is conditional SQL safe from injection?

**A: Yes — completely safe.**

The `#if` preprocessor **only allows**:

- Parameter variables using `${param}` (e.g. `${user_id}`)
- String literals (`'active'`, `"pending"`)
- Numbers and basic operators
- Whitespace and comments

Raw variable names without `${...}` or any attempt to inject raw SQL will raise a parsing error **before** execution.

```python
# This will RAISE an exception "ValueError: Raw variable or invalid syntax..." (not execute!)
"#if ${user_id}; DROP TABLE t_user; --"
```

## Features Summary

| Feature                       | Notes                                                                           |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Connection pooling            | Via `minconn` / `maxconn`                                                       |
| Named queries                 | Stored in dictionary                                                            |
| Single-row / multi-row fetch  | `read_row()` / `read_rows()`                                                    |
| Single / batch CUD operations | `update()` / `updates()`                                                        |
| Output parameters             | Via `params_out` dict                                                           |
| Transactions via `with`       | Auto rollback on exception                                                      |
| Partially return CSV          | `read_csv_partial` / `read_csv_partial_async`                                   |
| Bilingual column aliases      | `"Name\|이름"` syntax                                                           |
| Conditional SQL               | `#if` / `#elif` / `#endif`                                                      |
| Dynamic Loop                  | `#foreach` / `#endfor` / `#endforeach`                                          |
| Include Query Snippet         | `#include` / `#include(key)`                                                    |
| Template Variable             | `${param}` MyBatis-style text substitution (e.g. dynamic table names)           |
| Logging support               | Before and after execute to DB via `before...` and `after...` callable function |
| SQL injection protection      | Strict parsing in conditionals                                                  |

## License

MIT (or as defined in your project)

---

Made with ❤️ for cleaner, safer SQLite code in Python.
