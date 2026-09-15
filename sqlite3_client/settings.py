"""settings"""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
class Settings:
    """db client settings"""

    database: str
    host: str = ""
    port: int = 0
    user: str = ""
    password: str = ""

    minconn: int = 1
    maxconn: int = 5
    connect_timeout: int = 5
    timeout: float = 5.0

    use_en_ko_column_alias: bool = False
    """SELECT file_name "File Name|파일명" """
    use_conditional: bool = False
    """
    #if target == 'korea'
        FROM tbl_korea
    #else
        FROM tbl_vietnam
    #endif
    """
    all_query: dict[str, str | dict[str, str]] = field(default_factory=dict)
    """all query information"""

    before_read_execute: Callable[[str, dict, str, str], None] | None = None
    """
    qry_key: str, params: dict, qry_str: str, qry_with_value: str
    """
    after_read_execute: Callable[[str, int], None] | None = None
    """
    qry_key: str, duration: int
    """
    before_update_execute: (
        Callable[
            [str, dict, dict, str, str],
            None,
        ]
        | None
    ) = None
    """
    qry_key: str, params: dict, params_out: dict, qry_str: str, qry_with_value: str
    """
    after_update_execute: Callable[[str, int, dict, int], None] | None = None
    """
    qry_key: str, row_count: int, params_out: dict, duration: int
    """

    @property
    def key(self):
        """key for another dictionary"""

        return (
            f"{self.host},{self.port},{self.database},{self.user},{self.password}"
            f"{self.minconn},{self.maxconn},{self.connect_timeout}"
        )
