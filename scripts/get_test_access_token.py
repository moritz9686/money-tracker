"""Copy a temporary Supabase test-user access token to the macOS clipboard."""

import getpass
import json
import subprocess
from pathlib import Path

import httpx


def main() -> None:
    config = json.loads(Path("mobile/.env.json").read_text())
    email = input("Test email: ").strip()
    password = getpass.getpass("Test password: ")
    response = httpx.post(
        f"{config['SUPABASE_URL']}/auth/v1/token",
        params={"grant_type": "password"},
        headers={
            "apikey": config["SUPABASE_PUBLISHABLE_KEY"],
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password},
        timeout=15,
    )
    if response.status_code != 200:
        raise SystemExit(
            "Login failed. Check the test credentials and confirm the user in Supabase."
        )
    token = response.json().get("access_token")
    if not isinstance(token, str) or not token:
        raise SystemExit("Supabase did not return an access token.")
    subprocess.run(["pbcopy"], input=token, text=True, check=True)
    print("Temporary access token copied to clipboard.")


if __name__ == "__main__":
    main()
