from typing import Generic, TypeVar

from pydantic import BaseModel

Z = TypeVar("Z")


class SQLGenericSearch(BaseModel, Generic[Z]):
    field: Z
    value: str
    use_ilike: bool = False
