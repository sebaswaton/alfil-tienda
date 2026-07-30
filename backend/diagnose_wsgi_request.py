"""Exercise the Passenger WSGI callable with a synthetic health request."""

from __future__ import annotations

import io
import os
import traceback
from pathlib import Path


REPORT_PATH = Path(__file__).with_name("cpanel-wsgi-diagnostic.txt")


def redact(text: object) -> str:
    value = str(text)
    for name in ("DATABASE_URL", "MEDIA_SIGNING_SECRET", "MEDIA_ADMIN_API_KEY"):
        secret = os.getenv(name)
        if secret:
            value = value.replace(secret, f"<{name}_REDACTED>")
    return value


def main() -> None:
    result: list[str] = ["ALFIL CPANEL WSGI REQUEST DIAGNOSTIC"]
    response: dict[str, object] = {}

    def start_response(status, headers, exc_info=None):
        response["status"] = status
        response["headers"] = headers

    environ = {
        "REQUEST_METHOD": "GET",
        "SCRIPT_NAME": "/alfil-api",
        "PATH_INFO": "/api/health",
        "QUERY_STRING": "",
        "SERVER_NAME": "alfilcc.com.pe",
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "CONTENT_LENGTH": "0",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    try:
        from passenger_wsgi import application

        body = b"".join(application(environ, start_response))
        result.append(f"Status: {response.get('status')}")
        result.append(f"Headers: {response.get('headers')}")
        result.append(f"Body: {body.decode('utf-8', errors='replace')}")
    except Exception as exc:
        result.append(f"ERROR: {type(exc).__name__}: {redact(exc)}")
        result.append(redact(traceback.format_exc()))

    REPORT_PATH.write_text("\n".join(result) + "\n", encoding="utf-8")
    print(f"Diagnostic written to {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
