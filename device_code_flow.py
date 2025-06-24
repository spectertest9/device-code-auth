#!/usr/bin/env python3
import os
import sys
import time
import webbrowser
import requests


def device_code_flow():
    client_id = os.getenv("GITHUB_CLIENT_ID", "a945f87ad537bfddb109")
    scope = os.getenv("GITHUB_SCOPE", "")
    response = requests.post(
        "https://github.com/login/device/code",
        data={"client_id": client_id, "scope": scope},
        headers={"Accept": "application/json"},
    )
    if response.status_code != 200:
        print("Error requesting device code:", response.status_code, response.text, file=sys.stderr)
        sys.exit(1)
    data = response.json()
    print(f"Visit {data['verification_uri']} and enter the code {data['user_code']}")
    try:
        webbrowser.open(data["verification_uri"])
    except Exception:
        pass
    input("Press Enter after you have completed authorization...")
    interval = int(data.get("interval", 5))
    while True:
        time.sleep(interval)
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "device_code": data["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
#!/usr/bin/env python3
import os
import sys
import time
import webbrowser
import requests


def device_code_flow():
    client_id = os.getenv("GITHUB_CLIENT_ID", "a945f87ad537bfddb109")
    scope = os.getenv("GITHUB_SCOPE", "")
    response = requests.post(
        "https://github.com/login/device/code",
        data={"client_id": client_id, "scope": scope},
        headers={"Accept": "application/json"},
    )
    if response.status_code != 200:
        print("Error requesting device code:", response.status_code, response.text, file=sys.stderr)
        sys.exit(1)
    data = response.json()
    print(f"Visit {data['verification_uri']} and enter the code {data['user_code']}")
    try:
        webbrowser.open(data["verification_uri"])
    except Exception:
        pass
    input("Press Enter after you have completed authorization...")
    interval = int(data.get("interval", 5))
    while True:
        time.sleep(interval)
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": client_id,
                "device_code": data["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            print("Error polling token:", token_resp.status_code, token_resp.text, file=sys.stderr)
            sys.exit(1)
        token_data = token_resp.json()
        if "error" in token_data:
            err = token_data["error"]
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 5
                continue
            print("Error:", token_data, file=sys.stderr)
            sys.exit(1)
        access_token = token_data["access_token"]
        print("Obtained access token.")
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
        )
        if user_resp.status_code == 200:
            print("Authenticated as", user_resp.json().get("login"))
        else:
            print("Token verification failed:", user_resp.status_code, user_resp.text, file=sys.stderr)
        return


if __name__ == "__main__":
    device_code_flow()
        if token_resp.status_code != 200:
            print("Error polling token:", token_resp.status_code, token_resp.text, file=sys.stderr)
            sys.exit(1)
        token_data = token_resp.json()
        if "error" in token_data:
            err = token_data["error"]
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 5
                continue
            print("Error:", token_data, file=sys.stderr)
            sys.exit(1)
        access_token = token_data["access_token"]
        print("Obtained access token.")
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
        )
        if user_resp.status_code == 200:
            print("Authenticated as", user_resp.json().get("login"))
        else:
            print("Token verification failed:", user_resp.status_code, user_resp.text, file=sys.stderr)
        return


if __name__ == "__main__":
    device_code_flow()
