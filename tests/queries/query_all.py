"""query collection"""

# pylint: disable=relative-beyond-top-level
from .query_update import qry_dic as query_update
from .query_read import qry_dic as query_read

qry_all = [query_update, query_read]

all_query = {}
for qry_cur in qry_all:
    dup = all_query.keys() & qry_cur.keys()
    if dup:
        raise ValueError(
            f"duplicated keys: {dup} in {all_query.keys()} and {qry_cur.keys()}"
        )

    all_query |= qry_cur
