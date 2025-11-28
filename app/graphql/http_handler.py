from datetime import datetime, timezone

from ariadne.asgi.handlers import GraphQLHTTPHandler
from starlette.requests import Request
from starlette.responses import Response

from app.core import ms_config


class HTTPHandler(GraphQLHTTPHandler):
    def _set_cookie(self, response: Response, key: str, value: str, front_localdev: bool, expires: datetime):
        response.set_cookie(
            key=key,
            value=value,
            expires=expires,
            httponly=ms_config.cookies.httponly,
            samesite="none" if front_localdev else "strict",
            secure=False if front_localdev else True,
        )

    def _delete_cookie(self, response: Response, key: str, front_localdev: bool):
        response.delete_cookie(
            key=key,
            samesite="none" if front_localdev else "strict",
        )

    async def create_json_response(
        self,
        request: Request,
        result: dict,
        success: bool,
    ) -> Response:
        response = await super().create_json_response(request, result, success)
        refresh_token = getattr(request, "_set_cookie_refresh_token", None)
        temporary_token = getattr(request, "_set_cookie_temporary_token", None)
        reminded_mfa_device = getattr(request, "_set_cookie_reminded_mfa_device", None)

        front_localdev = (
            True
            if ms_config.is_dev_environment() and request.client and request.client.host.endswith("localdev.tikee.io")
            else False
        )

        if refresh_token:
            expires = datetime.now(tz=timezone.utc) + ms_config.cookies.refresh_token_duration
            self._set_cookie(response, "refresh_token", refresh_token, front_localdev, expires)

        if temporary_token:
            expires = datetime.now(tz=timezone.utc) + ms_config.cookies.temporary_token_duration
            self._set_cookie(response, "temporary_token", temporary_token, front_localdev, expires)

        if reminded_mfa_device:
            expires = datetime.now(tz=timezone.utc) + ms_config.cookies.reminded_mfa_device_expires_after
            self._set_cookie(response, "reminded_mfa_device", reminded_mfa_device, front_localdev, expires)

        if getattr(request, "_remove_refresh_token", None):
            self._delete_cookie(response, "refresh_token", front_localdev)

        if getattr(request, "_remove_temporary_token", None):
            self._delete_cookie(response, "temporary_token", front_localdev)

        return response
