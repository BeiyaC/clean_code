from collections.abc import Iterable
from typing import Any, Dict, List, Optional, TypedDict


class PageInfo(TypedDict):
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]


class BaseEdge(TypedDict):
    node: Dict[str, Any]
    cursor: str


class BasePaginatedResponse(TypedDict):
    edges: List[BaseEdge]
    nodes: Iterable[Dict[str, Any]]
    page_info: PageInfo
    total_count: int
