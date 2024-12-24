from typing import Dict, List

import requests

from bot.creds import FASTAPI_BASE_URL


def get_all_users() -> List[Dict]:
    """
    Make a request to the API server to get all users.

    Returns:
        List[Dict]: List of users with all fields.
    """
    url = f"{FASTAPI_BASE_URL}/get_all_users"
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        return []
    data = response.json()
    return data.get("data", {}).get("users", [])
