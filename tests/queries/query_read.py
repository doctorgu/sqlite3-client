"""query for user"""

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
        "read_user_search": """
SELECT  user_id, user_name, user_rank, insert_time, update_time
FROM    t_user
WHERE   1 = 1
#if user_id
        AND user_id = :user_id
#elif user_name
        AND user_name LIKE :user_name
#elif user_rank
        AND user_rank <= :user_rank
#endif
"""
    }
)

qry_dic.update(
    {
        "read_user_alias": """
SELECT  user_id "Id|아이디", user_name "Name|이름", user_rank "Rank|순위"
FROM    t_user
WHERE   user_id = :user_id
"""
    }
)

qry_dic.update(
    {
        "read_csv_partial": """
WITH RECURSIVE dates(rnum, d) AS (
    VALUES(1, '2001-01-01')
    UNION ALL
    SELECT  rnum + 1, date(d, '+1 day')
    FROM    dates
    WHERE   d < '2025-12-31'
)
SELECT  rnum,
        strftime('%Y년 %m월 %d일', d) each_day
FROM    dates
"""
    }
)

qry_dic.update(
    {
        "insert_python_join": """
INSERT INTO python_join (
        repository, file_path, fn_name, line_no, join_type,
        left_table, left_column, right_table, right_column
)
SELECT
        :repository, :file_path, :fn_name, :line_no, :join_type,
        :left_table, :left_column, :right_table, :right_column
"""
    }
)
