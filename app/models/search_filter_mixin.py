from typing import Any, Iterable, Type, TypeVar

from sqlalchemy.sql.expression import Select

from app.models.base_model import Base
from app.models.types import SQLGenericSearch

T = TypeVar("T", bound=Base)
V = TypeVar("V", bound=Any)


class SearchFilterMixin:
    def build_search_filters(
        self, class_name: Type[T], stmt: Select[V], search: Iterable[SQLGenericSearch]
    ) -> Select[V]:
        for values in search:
            if values.use_ilike:
                stmt = stmt.where(getattr(class_name, values.field.value).ilike(f"%{values.value}%"))
            else:
                stmt = stmt.where(getattr(class_name, values.field.value) == values.value)

        return stmt
