"""test client with real sqlite database"""

import os

import pytest

from sqlite3_client.client import Client
from tests.db_settings import db_settings


@pytest.fixture(autouse=True)
def cleanup_db():
    test_db_path = "test.db"
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass
    yield
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except OSError:
            pass


def test_real_sqlite_crud():
    """test all CRUD operations against real SQLite"""
    db_client = Client(db_settings=db_settings)

    # 1. create_tables
    db_client.update("create_tables", {})

    # 2. upsert_user
    row_count = db_client.update(
        "upsert_user",
        {"user_id": "gildong.hong", "user_name": "홍길똥", "user_rank": 1},
    )
    assert row_count == 1

    # 3. upsert_user_params_out
    params_out = {"user_name": "", "user_rank": 0}
    db_client.update(
        "upsert_user",
        {"user_id": "gildong.hong", "user_name": "홍길동", "user_rank": 1},
        params_out,
    )
    assert params_out["user_name"] == "홍길동"
    assert params_out["user_rank"] == 1

    # 4. upsert_user_list
    batch = [
        (
            "upsert_user",
            {"user_id": "sunja.kim", "user_name": "김순자", "user_rank": 2},
        ),
        (
            "upsert_user",
            {"user_id": "malja.kim", "user_name": "김말자", "user_rank": 3},
        ),
    ]
    row_counts = db_client.updates(batch)
    assert row_counts == [1, 1]

    # 5. read_user_one_row
    row = db_client.read_row("read_user_id_all", {})
    assert row is not None
    assert "user_id" in row.keys()

    # 6. read_user_all_rows
    rows = db_client.read_rows("read_user_id_all", {})
    assert len(rows) == 3

    # 7. read_using_conditional
    rows_c1 = db_client.read_rows(
        "read_user_search",
        {"user_id": "gildong.hong", "user_name": "", "user_rank": 0},
    )
    assert [r["user_name"] for r in rows_c1] == ["홍길동"]

    rows_c2 = db_client.read_rows(
        "read_user_search",
        {"user_id": "", "user_name": "%김%", "user_rank": 0},
    )
    assert sorted([r["user_name"] for r in rows_c2]) == ["김말자", "김순자"]

    rows_c3 = db_client.read_rows(
        "read_user_search",
        {"user_id": "", "user_name": "", "user_rank": 3},
    )
    assert sorted([r["user_name"] for r in rows_c3]) == ["김말자", "김순자", "홍길동"]

    # 7-1. read_using_include (#include)
    rows_i1 = db_client.read_rows(
        "read_user_by_key",
        {"user_id": "gildong.hong", "user_name": "", "user_rank": 0},
    )
    assert [r["user_id"] for r in rows_i1] == ["gildong.hong"]

    rows_i2 = db_client.read_rows(
        "read_user_by_key",
        {"user_id": "", "user_name": "%김%", "user_rank": 0},
    )
    assert sorted([r["user_id"] for r in rows_i2]) == ["malja.kim", "sunja.kim"]

    rows_i3 = db_client.read_rows(
        "read_user_by_key",
        {"user_id": "", "user_name": "", "user_rank": 3},
    )
    assert sorted([r["user_id"] for r in rows_i3]) == [
        "gildong.hong",
        "malja.kim",
        "sunja.kim",
    ]

    # 8. bilingual alias
    rows_en = db_client.read_rows(
        "read_user_alias", {"user_id": "gildong.hong"}, en=True
    )
    assert rows_en[0]["Id"] == "gildong.hong"
    assert rows_en[0]["Name"] == "홍길동"

    rows_ko = db_client.read_rows(
        "read_user_alias", {"user_id": "gildong.hong"}, en=False
    )
    assert rows_ko[0]["아이디"] == "gildong.hong"
    assert rows_ko[0]["이름"] == "홍길동"

    # 9. transaction with rollback
    try:
        with Client(db_settings=db_settings) as tx_client:
            tx_client.update(
                "upsert_user",
                {"user_id": "temp.user", "user_name": "임시", "user_rank": 99},
            )
            raise RuntimeError("intentional rollback")
    except RuntimeError:
        pass

    check_row = db_client.read_row(
        "read_user_search", {"user_id": "temp.user", "user_name": "", "user_rank": 0}
    )
    assert check_row is None

    # 10. read_csv_partial
    csv_gen = db_client.read_csv_partial("read_csv_partial", {}, row_count_partial=10)
    bom = next(csv_gen)
    assert bom == b"\xef\xbb\xbf"
    first_chunk = next(csv_gen)
    assert b"rnum,each_day" in first_chunk


@pytest.mark.asyncio
async def test_real_sqlite_csv_async():
    """test streaming CSV export with async"""
    db_client = Client(db_settings=db_settings)
    chunks = []
    async for chunk in db_client.read_csv_partial_async(
        "read_csv_partial", {}, row_count_partial=10
    ):
        chunks.append(chunk)
        if len(chunks) >= 3:
            break
    assert chunks[0] == b"\xef\xbb\xbf"
    assert b"rnum,each_day" in chunks[1]


def test_real_sqlite_multi_statement_semicolon():
    """test that update with multiple statements separated by semicolon works"""
    db_client = Client(db_settings=db_settings)

    # 1. Multiple DDL statements separated by semicolon
    db_client.qry.qry_settings.all_query["create_multi_tables"] = (
        'CREATE TABLE "t_multi_a" (id int, val text);\n'
        'CREATE UNIQUE INDEX "t_multi_a_idx" ON "t_multi_a" (id);'
    )
    db_client.update("create_multi_tables", {})

    # 2. Multiple DML statements with semicolon in string literal
    db_client.qry.qry_settings.all_query["insert_multi"] = (
        "INSERT INTO \"t_multi_a\" VALUES (1, 'hello;world');\n"
        "INSERT INTO \"t_multi_a\" VALUES (2, 'second;value');"
    )
    row_count = db_client.update("insert_multi", {})
    assert row_count == 1

    # Verify rows were inserted
    db_client.qry.qry_settings.all_query["read_multi_a"] = (
        'SELECT id, val FROM "t_multi_a" ORDER BY id'
    )
    rows = db_client.read_rows("read_multi_a", {})
    assert len(rows) == 2
    assert rows[0]["val"] == "hello;world"
    assert rows[1]["val"] == "second;value"
