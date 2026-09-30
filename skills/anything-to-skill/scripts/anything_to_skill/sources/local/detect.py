from pathlib import Path

NAME = 'local'


def detect(arg: str) -> int:
    try:
        return 10 if Path(arg).expanduser().exists() else 0
    except OSError:
        return 0
