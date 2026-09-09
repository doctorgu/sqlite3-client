"""query for schema"""

qry_dic: dict[str, str] = {}

qry_dic.update(
    {
        "create_tables": """
CREATE TABLE IF NOT EXISTS t_user (
    user_id VARCHAR(50) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    user_rank INT NOT NULL,
    insert_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT t_user_pkey PRIMARY KEY (user_id)
)
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

qry_dic.update(
    {
        "delete_user": """
DELETE
FROM    t_user
WHERE   user_id = :user_id
"""
    }
)
