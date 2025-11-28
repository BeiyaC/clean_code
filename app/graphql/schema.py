import os

from ariadne import load_schema_from_path, snake_case_fallback_resolvers
from ariadne.contrib.federation.schema import make_federated_schema

from app.graphql.mutation import mutation_type
from app.graphql.resolver import resolver_type
from app.graphql.scalars.uuid import uuid_scalar

type_defs = load_schema_from_path(f"{os.getcwd()}/app/graphql/schema.graphql")
schema = make_federated_schema(
    type_defs,
    mutation_type,
    resolver_type,
    uuid_scalar,
    snake_case_fallback_resolvers,
)
