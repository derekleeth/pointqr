from __future__ import annotations

from slowapi import Limiter
from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    """Extract real client IP address with Cloudflare, proxy, and fallback priority.

    Checks in order:
      1. CF-Connecting-IP (authoritative client IP passed by Cloudflare)
      2. X-Real-IP (set by Nginx from $remote_addr after real_ip resolution)
      3. X-Forwarded-For (first entry in client proxy chain)
      4. request.client.host (ASGI connection client address)
    """
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


limiter = Limiter(key_func=get_client_ip)

