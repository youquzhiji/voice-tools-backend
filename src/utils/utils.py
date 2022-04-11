import multiprocessing
import platform
import random
import string
from pathlib import Path

from cpuinfo import cpuinfo

from constants import version


def generate_token(length: int = 2048) -> str:
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def load_token() -> str:
    path = Path('./config/token.txt')
    if path.is_file():
        return path.read_text('UTF-8').strip()
    else:
        token = generate_token()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token, 'UTF-8')
        return load_token()


def get_worker_info():
    cpu_info = cpuinfo.get_cpu_info()
    cpu_info['flags'] = None

    return {'token': load_token(), 'version': version, 'cpu_count': multiprocessing.cpu_count(),
            'platform': platform.platform(), 'os': platform.system(), 'cpu': cpu_info}

