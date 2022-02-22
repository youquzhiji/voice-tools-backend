import random
import string

from constants import version


def generate_token(length: int = 2048):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def get_server_info():
    return {'token': generate_token(), 'version': version}
