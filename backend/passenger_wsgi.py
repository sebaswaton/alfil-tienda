"""Synchronous ASGI-to-WSGI entry point for cPanel Passenger."""

import asyncio
import os
import sys
from http import HTTPStatus

sys.path.insert(0, os.path.dirname(__file__))

from app.main import app as fastapi_app


def _headers_from_environ(environ):
    headers = []
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].replace("_", "-").lower().encode("latin-1")
            headers.append((name, str(value).encode("latin-1")))

    if environ.get("CONTENT_TYPE"):
        headers.append((b"content-type", environ["CONTENT_TYPE"].encode("latin-1")))
    if environ.get("CONTENT_LENGTH"):
        headers.append(
            (b"content-length", environ["CONTENT_LENGTH"].encode("latin-1"))
        )
    return headers


def _scope_from_environ(environ):
    server_name = environ.get("SERVER_NAME", "localhost")
    try:
        server_port = int(environ.get("SERVER_PORT", "443"))
    except ValueError:
        server_port = 443

    path = environ.get("PATH_INFO", "") or "/"
    root_path = environ.get("SCRIPT_NAME", "")

    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").split("/")[-1],
        "method": environ.get("REQUEST_METHOD", "GET"),
        "scheme": environ.get("wsgi.url_scheme", "https"),
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": environ.get("QUERY_STRING", "").encode("latin-1"),
        "root_path": root_path,
        "headers": _headers_from_environ(environ),
        "server": (server_name, server_port),
        "client": (environ.get("REMOTE_ADDR", ""), 0),
    }


def _run_asgi(environ):
    scope = _scope_from_environ(environ)
    body = environ["wsgi.input"].read(
        int(environ.get("CONTENT_LENGTH") or 0)
    )
    request_sent = False
    status = 500
    headers = [(b"content-type", b"text/plain")]
    chunks = []

    async def receive():
        nonlocal request_sent
        if not request_sent:
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        nonlocal status, headers
        if message["type"] == "http.response.start":
            status = message["status"]
            headers = message.get("headers", [])
        elif message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))

    asyncio.run(fastapi_app(scope, receive, send))
    return status, headers, b"".join(chunks)


def application(environ, start_response):
    base_path = os.getenv("APPLICATION_BASE_PATH", "").rstrip("/")
    normalized = environ.copy()
    path_info = normalized.get("PATH_INFO", "") or "/"

    if base_path and (
        path_info == base_path or path_info.startswith(base_path + "/")
    ):
        normalized["SCRIPT_NAME"] = base_path
        normalized["PATH_INFO"] = path_info[len(base_path) :] or "/"

    status, headers, body = _run_asgi(normalized)
    phrase = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else ""
    start_response(
        f"{status} {phrase}",
        [
            (name.decode("latin-1"), value.decode("latin-1"))
            for name, value in headers
        ],
    )
    return [body]
