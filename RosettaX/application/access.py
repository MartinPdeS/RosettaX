"""Deployment mode and shared access checks for administration pages."""

import hmac
import os
from flask import Response, current_app, has_request_context, redirect, request
from html import escape
from itsdangerous import BadData, URLSafeTimedSerializer

HOSTED_CONFIG_KEY = "ROSETTAX_HOSTED"
ADMIN_TOKEN_ENV_VAR = "ROSETTAX_ADMIN_TOKEN"
ADMIN_COOKIE = "rosettax-admin"
ADMIN_SESSION_SECONDS = 30 * 60
ADMIN_DESTINATIONS = {"/admin", "/settings"}


def is_hosted() -> bool:
    """Return whether this request is served by the hosted entry point."""
    return has_request_context() and bool(current_app.config.get(HOSTED_CONFIG_KEY))


def get_admin_token() -> str:
    """Read the administrator credential from the server environment."""
    return os.getenv(ADMIN_TOKEN_ENV_VAR, "").strip()


def matches_admin_token(*, candidate: str) -> bool:
    """Compare the submitted credential with the configured credential."""
    token = get_admin_token()
    return bool(token) and hmac.compare_digest(
        token.encode(), candidate.strip().encode()
    )


def _admin_serializer(*, token: str) -> URLSafeTimedSerializer:
    """Build the signer used by all workers for administrator sessions."""
    return URLSafeTimedSerializer(token, salt="rosettax-admin-session")


def has_admin_session() -> bool:
    """Verify the signed administrator cookie and its expiry on every request."""
    token = get_admin_token()
    if not token or not has_request_context():
        return False
    cookie = request.cookies.get(ADMIN_COOKIE)
    if not cookie:
        return False
    try:
        return (
            _admin_serializer(token=token).loads(cookie, max_age=ADMIN_SESSION_SECONDS)
            == "admin"
        )
    except BadData:
        return False


def can_edit_settings() -> bool:
    """Allow local editing and require administrator access on hosted requests."""
    return not is_hosted() or has_admin_session()


def admin_login() -> Response:
    """Exchange a submitted administrator credential for a short-lived cookie."""
    destination = request.args.get("next", "/admin")
    if destination not in ADMIN_DESTINATIONS:
        destination = "/admin"

    token = get_admin_token()
    error = ""
    status = 200
    if not token:
        error = "Administrator access is unavailable on this server."
        status = 404
    elif request.method == "POST":
        if matches_admin_token(candidate=request.form.get("token", "")):
            response = redirect(destination, code=303)
            response.set_cookie(
                ADMIN_COOKIE,
                _admin_serializer(token=token).dumps("admin"),
                max_age=ADMIN_SESSION_SECONDS,
                secure=is_hosted() or request.is_secure,
                httponly=True,
                samesite="Strict",
            )
            response.headers["Cache-Control"] = "no-store"
            return response
        error = "The administrator token was incorrect."
        status = 403

    form = ""
    if token:
        form = f"""
        <form method="post" action="/admin/login?next={escape(destination, quote=True)}">
            <label for="token">Administrator token</label>
            <input id="token" name="token" type="password" autocomplete="current-password" required>
            <button type="submit">Sign in</button>
        </form>"""
    return Response(
        f"""<!doctype html>
        <html lang="en"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="/assets/admin-login.css">
        <title>Administrator sign-in · RosettaX</title></head>
        <body class="rosettax-admin-login"><main><h1>Administrator sign-in</h1>
        <p role="status">{escape(error)}</p>{form}
        <a href="/">Return to RosettaX</a></main></body></html>""",
        status=status,
        mimetype="text/html",
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )
