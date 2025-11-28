from typing import Optional

from pydantic import BaseModel


class PaginationInfoDto(BaseModel):
    limit: int
    offset: int


def generate_pagination_dto(
    default_size: int,
    max_size: int,
    first: Optional[int],
    last: Optional[int],
    before: Optional[int],
    after: Optional[int],
) -> PaginationInfoDto:
    if (
        after is not None
        and (before is not None or last is not None)
        or first is not None
        and (last is not None or before is not None)
        or (last is not None and before is None)
    ):
        raise ValueError('Bad combinaisons between "after", "before", "first" and "last" parameters.')
    if after is not None:
        offset = after
        if first is not None:
            limit = first
        else:
            limit = default_size
    elif before is not None:
        if last is not None:
            limit = last
        else:
            limit = default_size
        offset = before - limit - 1

        if offset < 0:
            limit = limit + offset
            offset = 0
    else:
        offset = 0
        limit = first if first is not None else default_size

    if limit > max_size:
        raise ValueError(f"Page length must be < {max_size}")

    return PaginationInfoDto(offset=offset, limit=limit)
