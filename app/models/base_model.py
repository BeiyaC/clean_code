from collections import Counter
from typing import Any, Dict

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing_extensions import Self


class Base(MappedAsDataclass, DeclarativeBase):
    def fill_model_with_dict(self, data: Dict[str, Any]) -> Self:
        for key, value in data.items():
            setattr(self, key, value)
        return self

    # I don't want to override __eq__ method on SQLAlchemy but idk if there will be any
    # side effects on SQLAlchemy.
    # TODO: This method does not manage relationships yet...
    def compare_with_other_model(self, model: Self) -> bool:
        self_columns = inspect(type(self)).columns
        model_columns = inspect(type(model)).columns
        if self_columns.keys() != model_columns.keys():
            return False

        result = []
        for column_name in self_columns.keys():
            self_data, column_data = getattr(self, column_name), getattr(model, column_name)
            (
                result.append(Counter(self_data) == Counter(column_data))
                if isinstance(self_data, list) and isinstance(column_data, list)
                else result.append(self_data == column_data)
            )
        return all(result)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
