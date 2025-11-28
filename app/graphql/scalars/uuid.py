from typing import Any
from uuid import UUID

from ariadne import ScalarType

uuid_scalar = ScalarType("Uuid")


@uuid_scalar.serializer
def serialize_uuid(value: UUID) -> str:
    return str(value)


@uuid_scalar.value_parser
def parse_uuid(value: Any) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        raise ValueError("Invalid Uuid format")
