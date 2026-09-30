from urllib.parse import urlsplit

NAME = 'web'


def detect(arg: str) -> int:
    return 1 if urlsplit(arg).scheme in ('http', 'https') else 0
