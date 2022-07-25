from __future__ import annotations

from os import cpu_count

import numpy as np


# Number of threads for multithreaded compression
CPU_COUNT = cpu_count()

# Byte length of int
INT = 4


def bdict_encode(d: dict[str, bytes | str]) -> bytes:
    """
    Encode dictionary to a byte array.

    For each block:
    - Byte 0     - 8     : lk = A long value - the length (bytes) of the key string
    - Byte 8     - 16    : lv = A long value - the length (bytes) of the value byte array
    - Byte 16    - 16+lk : Key string bytes in utf-8
    - Byte 16+lk - 16+lk+lv : Byte array content

    :param d: Dict with string keys and bytes/string values
    :return: Encoded byte array
    """
    # Encode strings
    d: list[tuple[bytes, bytes]] = [
        (k.encode('utf8'), v.encode('utf-8') if isinstance(v, str) else v) for k, v in d.items()]

    # Count length
    total_len = sum([len(k) + len(v) + INT * 2 for k, v in d])

    # Create byte array
    b = bytearray(total_len)

    # Loop through all kv and write byte array
    i = 0
    for k, v in d:
        lk, lv = len(k), len(v)

        b[i: i + INT] = lk.to_bytes(INT, 'big')
        i += INT
        b[i: i + INT] = lv.to_bytes(INT, 'big')
        i += INT
        b[i: i + lk] = k
        i += lk
        b[i: i + lv] = v
        i += lv

    return bytes(b)
    # return ZSTD_compress(bytes(b), 19, CPU_COUNT)


def bdict_decode(b: bytes) -> dict[str, bytes]:
    """
    Decode byte array dictionary

    :param b:
    :return:
    """
    # b = ZSTD_uncompress(b)
    i = 0
    dic = {}

    # Loop through byte array
    while i < len(b):
        lk = int.from_bytes(b[i: i + INT], 'big')
        i += INT
        lv = int.from_bytes(b[i: i + INT], 'big')
        i += INT
        k = b[i: i + lk].decode('utf-8')
        i += lk
        v = b[i: i + lv]
        i += lv

        dic[k] = v

    return dic


if __name__ == '__main__':
    d = {'meow': 'hi', 'bytes': np.array([1, 2, 3, 4, 5]).tobytes()}
    print(d)
    print(bdict_encode(d))
    print(bdict_decode(bdict_encode(d)))
