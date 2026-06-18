import requests
import time
import webbrowser

GITHUB_CLIENT_ID = "Iv23liKOIHHPXoMZ5Byf"  # Public OAuth App client ID for GitHub Models
DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"


class GitHubAuth:
    """
    GitHub Device Flow OAuth.
    Opens the browser for the user to enter the device code,
    then polls until the token is granted.
    """

    def authenticate_device_flow(self) -> str:
        # Step 1: Request device code
        resp = requests.post(
            DEVICE_CODE_URL,
            headers={"Accept": "application/json"},
            data={"client_id": GITHUB_CLIENT_ID, "scope": "read:user"}
        )
        resp.raise_for_status()
        data = resp.json()

        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_uri = data["verification_uri"]
        interval = data.get("interval", 5)
        expires_in = data.get("expires_in", 900)

        # Step 2: Open browser and show code
        print(f"Opening browser. Enter code: {user_code}")
        webbrowser.open(verification_uri)

        # Step 3: Poll for token
        deadline = time.time() + expires_in
        while time.time() < deadline:
            time.sleep(interval)
            poll = requests.post(
                TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            poll_data = poll.json()
            if "access_token" in poll_data:
                return poll_data["access_token"]
            if poll_data.get("error") == "slow_down":
                interval += 5
            if poll_data.get("error") == "access_denied":
                raise PermissionError("GitHub sign-in was denied by the user.")

        raise TimeoutError("GitHub sign-in timed out. Please try again.")
