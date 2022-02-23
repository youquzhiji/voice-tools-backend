import random
import string
import multiprocessing
from pathlib import Path

from constants import version, token_path


def generate_token(length: int = 2048) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def load_token() -> str:
    path = Path(token_path)
    if path.is_file():
        return path.read_text('UTF-8').strip()
    else:
        token = generate_token()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token, 'UTF-8')
        return load_token()


def get_server_info():
    return {'token': load_token(), 'version': version, 'cpu_count': multiprocessing.cpu_count()}
