#!/usr/bin/env python3
"""
Simple script to demonstrate GitHub's device code authentication flow.

This script kicks off the device code grant on GitHub by requesting a
``device_code`` and ``user_code`` from the ``/login/device/code`` endpoint.
The user (that's you!) is then instructed to visit the provided
verification URL and enter the one‐time user code.  While you complete
the verification in your browser, this script polls GitHub's token
endpoint until an access token is granted.  Finally, it makes a test
request against the GitHub API to verify that the token works and
displays the authenticated username.

You can override the client ID or requested scopes by setting the
``GITHUB_CLIENT_ID`` or ``GITHUB_SCOPE`` environment variables.

The default client ID used here corresponds to GitHub's own CLI
application and does not require a client secret.  See the official
documentation for details:
https://docs.github.com/en/developers/apps/authorizing-oauth-apps#device-flow

Usage:

    python3 device_auth.py           # use defaults
    GITHUB_SCOPE=repo python3 device_auth.py

When running, the script will prompt you to navigate to the
verification URL in a browser.  It will also try to open the URL
automatically if your system supports it.

Note: the access token granted by this flow will have the scopes you
requested (if any) and is short lived.  Treat it like a password and
store it securely if you intend to reuse it.
"""

from __future__ import annotations

import json
import os
import sys
import time
import webbrowser
from urllib.parse import parse_qs

import requests



def request_device_code(client_id: str, scope: str = "") -> dict[str, str]:
    """Request a device and user code from GitHub.

    Args:
        client_id: The client ID of the GitHub OAuth application.
        scope: Optional space delimited scopes.  If omitted, no extra
            permissions are granted beyond reading basic account data.

    Returns:
        A dictionary containing the fields returned by GitHub.  At
        minimum this includes ``device_code``, ``user_code``,
        ``verification_uri``, ``expires_in`` and ``interval``.
    """
    url = "https://github.com/login/device/code"
    payload = {
        "client_id": client_id,
        "scope": scope,
    }
    resp = requests.post(url, data=payload, headers={"Accept": "application/json"})
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to request device code: HTTP {resp.status_code}: {resp.text!r}"
        )
    return resp.json()



def poll_access_token(client_id: str, device_code: str) -> str:
    """Poll GitHub until an access token is granted for the provided device code.

    This function blocks until the user finishes the verification step
    and GitHub returns an ``access_token`` or until the device code
    expires.

    Args:
        client_id: The client ID used to initiate the device flow.
        device_code: The device code returned from ``request_device_code``.

    Returns:
        The OAuth access token as a string.

    Raises:
        RuntimeError: If the device code expires without successful
            authorization or GitHub returns a non recoverable error.
    """
    token_url = "https://github.com/login/oauth/access_token"
    # According to GitHub's docs the interval is 5 seconds, but we'll
    # politely wait a bit longer on each poll in case GitHub asks us to
    # slow down.  We don't include a client secret because public
    # clients such as the GitHub CLI do not require one for device flow.
    # We'll initially sleep for the recommended interval and then adjust
    # based on server responses.
    interval = 5
    while True:
        time.sleep(interval)
        response = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to poll for access token: HTTP {response.status_code}: {response.text!r}"
            )
        data = response.json()
        # Handle error responses.  See https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow
        if "error" in data:
            err = data["error"]
            if err == "authorization_pending":
                # The user has not yet authorized.  Keep waiting.
                continue
            elif err == "slow_down":
                # Increase the polling interval.
                interval += 5
                continue
            elif err == "expired_token":
                raise RuntimeError("The device code has expired. Restart the flow.")
            else:
                # Other errors should halt the process.
                raise RuntimeError(f"Error polling for token: {err}: {data.get('error_description')}")
        # Success: we got a token!
        return data["access_token"]



def authenticate_and_print_user(client_id: str, scope: str = "") -> None:
    """Orchestrate the device code flow and print the authenticated user.

    This high-level helper handles requesting the device code, opening
    the browser for the user, polling for an access token and finally
    printing the username associated with the token.

    Args:
        client_id: The client ID of the OAuth app.
        scope: A space-delimited string of scopes to request.
    """
    info = request_device_code(client_id, scope)
    user_code = info["user_code"]
    verification_uri = info.get("verification_uri") or info.get("verification_uri_complete")
    expires_in = info["expires_in"]
    interval = info["interval"]
    print()
    print("=== GitHub Device Code Authentication ===")
    print(f"Please visit {verification_uri} and enter the following code when prompted:")
    print(f"\n    {user_code}\n")
    print(f"This code will expire in {expires_in} seconds. Press Enter once you've submitted it.")
    # Attempt to open the URL in the user's default browser
    try:
        webbrowser.open(verification_uri)
    except Exception:
        pass
    # Wait for the user to proceed
    input()
    print("Waiting for authorization... this may take a few moments.")
    token = poll_access_token(client_id, info["device_code"])
    print("Successfully obtained an access token.")
    # Use the token to call the GitHub API and print the authenticated username
    r = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}", "Accept": "application/json"},
    )
    if r.status_code == 200:
        login = r.json().get("login")
        print(f"Authenticated as: {login}")
    else:
        print(f"Warning: unable to verify token. HTTP {r.status_code}: {r.text}")


def main() -> None:
    # Determine the client ID and scopes from environment variables
    client_id = os.getenv("GITHUB_CLIENT_ID", "a945f87ad537bfddb109")
    scope = os.getenv("GITHUB_SCOPE", "")
    try:
        authenticate_and_print_user(client_id, scope)
    except Exception as exc:
        print(f"An error occurred during authentication: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
