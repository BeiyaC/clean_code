from typing import Dict, Optional

from ariadne.types import ContextValue
from starlette.requests import Request


async def get_context_value(request: Request, data: Optional[Dict] = None) -> ContextValue:
    return {"request": request, "data": data}
