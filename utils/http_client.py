"""
  @ Author:   Mr.Hat
  @ Date:     2024/4/11 13:36
  @ Description: 
  @ History:
"""
from curl_cffi.requests import AsyncSession
from fake_useragent import UserAgent


HEADERS = {
    'authority': 'api.xter.io',
    'accept': '*/*',
    'authorization': '',
    'content-type': 'application/json',
    'origin': 'https://xter.io',
    'referer': 'https://xter.io/',
    'user-agent': UserAgent().random,
    "Sensorsdatajssdkcross": "%7B%22distinct_id%22%3A%2218e9e863069113e-06deb59f7fe507c-3b435c3b-2073600-18e9e86306a18ba%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMThlOWU4NjMwNjkxMTNlLTA2ZGViNTlmN2ZlNTA3Yy0zYjQzNWMzYi0yMDczNjAwLTE4ZTllODYzMDZhMThiYSJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218e9e863069113e-06deb59f7fe507c-3b435c3b-2073600-18e9e86306a18ba%22%7D",
}


def async_http_client(proxy=None) -> AsyncSession:
    session = AsyncSession(impersonate="chrome120", timeout=60)

    if proxy:
        session.proxies.update({
            "http": "http://" + proxy,
            "https": "http://" + proxy,
        })

        session.headers.update(HEADERS)

        return session
