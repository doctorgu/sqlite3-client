"""client_util"""

import json
from datetime import datetime, date
from typing import Literal

# pylint: disable=relative-beyond-top-level
from .query_util import replace_en_ko_column_alias, get_conditional
from .settings import Settings


class Query:
    """query"""

    def __init__(self, qry_settings: Settings):
        self.qry_settings = qry_settings

    def get_query_by_key(
        self,
        qry_key: str,
        params: dict,
        func_type: Literal["update", "read", "csv"],
        en: bool = False,
    ) -> str:
        """get query string by qry_key"""

        def serial_date(obj):
            """JSON serializer for objects not serializable by default json code"""

            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        query = self.qry_settings.all_query.get(qry_key)
        if not query:
            raise KeyError(f"{qry_key} not exists")

        info = {
            "qry_key": qry_key,
            "params": params,
            "func_type": func_type,
            "en": en,
        }

        if self.qry_settings.use_en_ko_column_alias and isinstance(en, bool):
            query = replace_en_ko_column_alias(query, en)
        if self.qry_settings.use_conditional and "#if" in query:
            query = get_conditional(query, params)

        return (
            f"/* {json.dumps(info, ensure_ascii=False, default=serial_date)} */{query}"
        )
