"""query_by_key_util"""

import re
from datetime import datetime


def get_conditional(qry_str: str, params: dict) -> str:
    """
    return true or false part by condition.

    ex:
    SELECT  *
    FROM
    #if target == 'en'
            tbl_en
    #else
            tbl_ko
    #endif
    ->
    SELECT  *
    FROM
            tbl_en
    """

    def eval_safe(condition: str, params: dict) -> bool:
        """
        allow only params and operators for condition to call eval safely

        # assert eval_safe(':target == "A"', {"target": "A"}) is True
        # assert eval_safe(':target != "A"', {"target": "A"}) is False
        # assert eval_safe(":target == 123", {"target": 123}) is True
        # assert eval_safe(":target != 123", {"target": 123}) is False
        # assert eval_safe(":target123 == 123", {"target123": 123}) is True
        # assert eval_safe(":target123 != 123", {"target123": 123}) is False
        # assert eval_safe(':target == ""', {"target": ""}) is True
        # assert eval_safe(':target != ""', {"target": ""}) is False
        # assert eval_safe('"A" in :targets', {"targets": ["A", "B"]}) is True
        # assert eval_safe('"A" not in :targets', {"targets": ["A", "B"]}) is False
        # assert eval_safe(":t in [i for i in range(10)]", {"t": 1}) is True  # '[i' not in
        """

        # remove ':' from :target
        to_eval = re.sub(r":(\w+)", r"\1", condition)

        # remove
        # - double quoted string
        # - single quoted string
        # - digit
        to_check = re.sub(r"""(".*?"|'.*?'|\b\d+\b)""", "", to_eval)

        param_set = set([key for key in params])
        op_set = {
            "==",
            "!=",
            ">=",
            ">",
            "<=",
            "<",
            "+",
            "-",
            "/",
            "//",
            "*",
            "**",
            "and",
            "or",
            "not",
            "in",
            "True",
            "False",
        }
        allowed_set = param_set | op_set

        for word in to_check.split():
            if word not in allowed_set:
                raise ValueError(f"'{word}' not in {allowed_set}")

        # pylint:disable=eval-used
        return eval(to_eval, params)

    rets = []
    lines = qry_str.splitlines()

    is_include = True
    is_checked = False
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("#if") or line_strip.startswith("#elif"):
            if not is_checked:
                _, condition = line_strip.split(maxsplit=1)
                # pylint:disable=eval-used
                is_include = eval_safe(condition, params.copy())
                if is_include:
                    is_checked = True
            else:
                is_include = False
        elif line_strip.startswith("#else"):
            is_include = not is_checked
        elif line_strip.startswith("#endif"):
            is_include = True
            is_checked = False
        elif is_include:
            rets.append(line)

    return "\n".join(rets)


def rep_kv(query: str, tab_count: int, **kwargs) -> str:
    """
    replace {key} with value when `rev_ky("WHERE user_name = {key}", key="u.user_name")`
    """

    ret = query
    ret = re.sub(r"^", " " * 4 * tab_count, ret, flags=re.MULTILINE)
    for k, v in kwargs.items():
        ret = ret.replace("{" + k + "}", str(v))

    return ret


def get_query_with_value(qry_str: str, params: dict) -> str:
    """replace raw query to value filled query"""

    def escape_literal(value) -> str:
        ret = ""
        if isinstance(value, str):
            ret = "'" + value.replace("'", "''") + "'"
        elif isinstance(value, datetime):
            ret = f"'{value.strftime('%Y-%m-%d %H:%M:%S.%f')}'"
        elif isinstance(value, list):
            ret = str(value)
        elif value is None:
            ret = "NULL"
        else:
            ret = str(value)
        return ret

    query_replaced = qry_str
    for key, value in params.items():
        replace = escape_literal(value)
        query_replaced = re.sub(rf":{re.escape(key)}\b", replace, query_replaced)

    # {{}} -> {} : python
    query_replaced = query_replaced.replace("{{", "{").replace("}}", "}")

    return query_replaced


def replace_en_ko_column_alias(qry_str: str, en: bool) -> str:
    """ "
    return en part or ko part separated by '|' using en variable
    ex:
    tbl.obj_nm "File Name|파일명"
    ->
    tbl.obj_nm "File Name"
    """

    pattern = r'(?P<ws>\s)"(?P<en>[^"]+)\|(?P<ko>[^"]+)"'
    en_ko = "en" if en else "ko"
    repl = rf'\g<ws>"\g<{en_ko}>"'
    qry_str_new = re.sub(
        pattern, repl, qry_str, count=0, flags=re.MULTILINE | re.IGNORECASE
    )
    return qry_str_new
