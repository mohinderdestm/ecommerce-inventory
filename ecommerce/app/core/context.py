import contextvars
from typing import Optional

request_ip_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_ip", default=None)
