import base64
import os
from datetime import timedelta
from typing import Any

from pydantic import BaseModel, HttpUrl, StrictInt, StrictStr, TypeAdapter, field_validator

from app.core.base import BaseConfig, Database


class _Cookies(BaseModel, validate_default=True):
    max_session_duration: timedelta = timedelta(days=90)
    refresh_token_duration: timedelta = timedelta(days=30)
    temporary_token_duration: timedelta = timedelta(days=180)
    reminded_mfa_device_expires_after: timedelta = timedelta(days=90)
    httponly: bool = True


class _JwtToken(BaseModel, validate_default=True):
    auth_public_key: StrictStr = os.environ["AUTH_PUBLIC_KEY"]
    auth_private_key: StrictStr = os.environ["AUTH_PRIVATE_KEY"]
    algorithm: StrictStr = "RS256"
    expires_in_seconds: StrictInt = 900
    issuer: StrictStr = "spicoo_app_core_server"

    @field_validator("auth_public_key", "auth_private_key", mode="before")
    @classmethod
    def decode_key(cls, data: Any) -> str:
        assert isinstance(data, str), "public and private key must be string"
        return base64.b64decode(data.replace("\\n", "\n")).decode("utf-8").replace("\\n", "\n")


class _Config(BaseConfig):
    database: Database = Database(
        host=os.environ["DATABASE_HOST"],
        port=int(os.environ["DATABASE_PORT"]),
        database=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USER"],
        password=os.environ["DATABASE_PASSWORD"],
    )
    graphql_gateway_url: str = str(TypeAdapter(HttpUrl).validate_python(os.environ["GRAPHQL_GATEWAY_URL"]))  # type: ignore # see: https://github.com/microsoft/pyright/discussions/7091
    web_application_url: str = str(TypeAdapter(HttpUrl).validate_python(os.environ["WEB_APPLICATION_URL"]))  # type: ignore # see: https://github.com/microsoft/pyright/discussions/7091
    cookies: _Cookies = _Cookies()
    jwt: _JwtToken = _JwtToken()
    reset_password_token_expires_after: int = 900
