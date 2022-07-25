from __future__ import annotations

import numpy as np


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
    total_len = sum([len(k) + len(v) + 16 for k, v in d])

    # Create byte array
    b = bytearray(total_len)

    # Loop through all kv and write byte array
    i = 0
    for k, v in d:
        lk, lv = len(k), len(v)

        b[i: i + 8] = lk.to_bytes(8, 'big')
        i += 8
        b[i: i + 8] = lv.to_bytes(8, 'big')
        i += 8
        b[i: i + lk] = k
        i += lk
        b[i: i + lv] = v
        i += lv

    return bytes(b)
