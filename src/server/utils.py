import random
import string
import multiprocessing
import time
from pathlib import Path

from constants import version, token_path
from server.temp import make_pi


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


def benchmark() -> float:
    """This function should return a benchmark number that higher means faster"""
    print('Running benchmark...')
    start = time.time()

    a = [d for d in make_pi(20000)]

    end = time.time()
    bench = 1 / (end - start) * 100
    print(f'> Benchmark finished: {bench:.2f}')

    return bench


def get_server_info():
    return {'token': load_token(), 'version': version, 'cpu_count': multiprocessing.cpu_count(),
            'benchmark': benchmark()}
