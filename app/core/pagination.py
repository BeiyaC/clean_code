import base64
from functools import wraps
from typing import Any, Awaitable, Callable, Iterable, Optional, Tuple, Type

from app.core.page_info import generate_pagination_dto
from app.core.exceptions import BadUserInputError
from app.core.type_pagination import BaseEdge, BasePaginatedResponse, PageInfo


def get_relay_node_cursor(position):
    return base64.b64encode(str(position).encode("utf-8")).decode("utf-8")


def relay_cursor_to_int(cursor: str) -> int:
    return int(base64.b64decode(cursor).decode("utf-8"))


def paginate(
    response_class: Type[BasePaginatedResponse] = BasePaginatedResponse,
    edge_class: Type[BaseEdge] = BaseEdge,
    max_size: int = 20,
    default_size: int = 20,
) -> Callable:
    def decorator_paginate(func: Callable[..., Awaitable[Tuple[Iterable, int]]]):
        @wraps(func)
        async def inner(
            *args: Any,
            first: Optional[int] = None,
            last: Optional[int] = None,
            before: Optional[str] = None,
            after: Optional[str] = None,
            **kwargs: Any,
        ):
            try:
                dto = generate_pagination_dto(
                    default_size,
                    max_size,
                    first,
                    last,
                    before=None if before is None else relay_cursor_to_int(before),
                    after=None if after is None else relay_cursor_to_int(after),
                )
            except ValueError as err:
                raise BadUserInputError(str(err))

            results, total_count = await func(*args, pagination_dto=dto, **kwargs)

            edges = [
                edge_class(node=node, cursor=get_relay_node_cursor(position + 1 + dto.offset))
                for position, node in enumerate(results)
            ]

            stop = dto.offset + len(edges)

            return response_class(
                edges=edges,
                nodes=results,
                page_info=PageInfo(
                    has_next_page=stop < total_count,
                    has_previous_page=dto.offset > 0,
                    start_cursor=get_relay_node_cursor(dto.offset + 1) if total_count else None,
                    end_cursor=get_relay_node_cursor(stop) if total_count else None,
                ),
                total_count=total_count,
            )

        return inner

    return decorator_paginate
