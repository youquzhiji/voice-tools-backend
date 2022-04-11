import platform
import random
import string
import multiprocessing
import time
from pathlib import Path

from cpuinfo import cpuinfo

from constants import version, token_path
from worker.temp import make_pi


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
    cpu_info = cpuinfo.get_cpu_info()
    cpu_info['flags'] = None

    return {'token': load_token(), 'version': version, 'cpu_count': multiprocessing.cpu_count(),
            'platform': platform.platform(), 'os': platform.system(), 'cpu': cpu_info}


class Timer:
    start: int

    def __init__(self):
        self.reset()

    def elapsed(self, reset: bool = True) -> float:
        t = (time.time_ns() - self.start) / 1000000
        if reset:
            self.reset()
        return t

    def log(self, *args):
        print(f'{self.elapsed():.0f}ms', *args)

    def reset(self):
        self.start = time.time_ns()

