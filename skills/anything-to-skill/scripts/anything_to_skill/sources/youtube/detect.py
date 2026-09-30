from urllib.parse import urlsplit

NAME = 'youtube'
_HOSTS = {
    'youtube.com',
    'www.youtube.com',
    'm.youtube.com',
    'music.youtube.com',
    'youtu.be',
}


def detect(arg: str) -> int:
    parts = urlsplit(arg)
    return 10 if parts.scheme in ('http', 'https') and parts.hostname in _HOSTS else 0
