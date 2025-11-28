from dataclasses import dataclass, field
from typing import Any, Dict, Generic, NotRequired, TypedDict, TypeVar

from httpx import USE_CLIENT_DEFAULT, AsyncClient, Headers, Response
from httpx._client import UseClientDefault
from httpx._types import AuthTypes, HeaderTypes
from pydantic import AliasChoices, AliasPath, BaseModel, Field, TypeAdapter, ValidationError

from app.core import ms_config as config
from app.core.logging import ctx_correlation_id, ctx_step


class GraphqlError(BaseModel):
    code: str | None = Field(validation_alias=AliasChoices(AliasPath("extensions", "code"), "code"))
    message: str


class GraphqlClientError(Exception):
    graphql_errors: list[GraphqlError]

    def __init__(self, error: list[GraphqlError] | None = None):
        self.graphql_errors = error or []


class GraphQLBody(TypedDict):
    query: str
    variables: NotRequired[Dict[str, Any]]


# TODO: replace this by PEP 695 https://github.com/pydantic/pydantic/issues/9782 is released
# see https://docs.pydantic.dev/latest/concepts/models/#generic-models
D = TypeVar("D", bound=BaseModel)


class GraphQLResponse(BaseModel, Generic[D]):
    data: D
    errors: list[GraphqlError] | None = None


@dataclass
class GraphQLClient[T: BaseModel]:
    _client: AsyncClient = field(
        default=AsyncClient(base_url=config.graphql_gateway_url),
        init=False,
    )

    @property
    def client(self):
        if self._client.is_closed:
            self._client = AsyncClient(base_url=config.graphql_gateway_url)
        return self._client

    def set_headers_context(self, headers: HeaderTypes | None = None) -> Headers:
        headers = Headers(headers)
        if not headers.get("correlation_id"):
            headers["correlation_id"] = str(ctx_correlation_id.get())
        if not headers.get("step"):
            headers["step"] = str(ctx_step.get() + 1)
        return headers

    async def run(
        self,
        json: GraphQLBody,
        response_body_class: type[T],
        auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
        headers: HeaderTypes | None = None,
    ) -> GraphQLResponse[T]:
        response = await self.client.post(
            "/v2/graphql", auth=auth, headers=self.set_headers_context(headers), json=json
        )

        return self._handle_response(response, response_body_class)

    def _handle_response(
        self,
        response: Response,
        response_body_class: type[T],
    ) -> GraphQLResponse[T]:
        response.raise_for_status()
        data = response.json()
        try:
            return GraphQLResponse[response_body_class].model_validate(data)
        except ValidationError as exc:
            type_adapter = TypeAdapter(list[GraphqlError])
            try:
                error = GraphqlClientError(type_adapter.validate_python(data.get("errors")))
            except Exception:
                error = GraphqlClientError()
            raise error from exc
