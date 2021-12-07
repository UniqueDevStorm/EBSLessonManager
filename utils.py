import requests


def HTTPRequest(url: str, method: str, **kwargs) -> dict:
    r = requests.request(url=url, method=method, **kwargs)
    return r.json()
