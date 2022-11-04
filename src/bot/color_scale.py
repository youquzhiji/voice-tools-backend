from __future__ import annotations

from typing import NamedTuple

import numpy as np
from numba import njit, uint8
from numpy import ndarray


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex: str) -> "RGB":
        """
        Create color from hex code
        >>> RGB.from_hex('#FFAAB7')
        RGB(r=255, g=170, b=183)
        :param hex: Hex color code
        :return: RGB object
        """
        while hex.startswith('#'):
            hex = hex[1:]

        r = int(hex[0:2], 16)
        g = int(hex[2:4], 16)
        b = int(hex[4:6], 16)
        return cls(r, g, b)

    def to_numpy(self) -> ndarray:
        """
        :return: uint8[:]
        """
        return np.array(self, dtype='uint8')

    def to_ansi_rgb(self, foreground: bool = True) -> str:
        c = '38' if foreground else '48'
        return f'\033[{c};2;{self.r};{self.g};{self.b}m'


def create_gradient_hex(colors: list[str], resolution: int = 300) -> ndarray:
    """
    Create gradient array from hex
    """
    colors = np.array([RGB.from_hex(s) for s in colors])
    return create_gradient(colors, resolution)


@njit(cache=True)
def create_gradient(colors: ndarray, resolution: int) -> ndarray:
    """
    Create gradient 2d array.

    Usage: arr[ratio / len(arr), :] = Scaled gradient color at that point
    """
    result = np.zeros((resolution * (len(colors) - 1), 3), dtype='uint8')

    # Create gradient mapping
    for i in range(len(colors) - 1):
        c1 = colors[i, :]
        c2 = colors[i + 1, :]
        bi = i * resolution

        for r in range(resolution):
            ratio = r / resolution
            result[bi + r, :] = c2 * ratio + c1 * (1 - ratio)

    return result


@njit(cache=True)
def get_raw(gradient: ndarray | uint8[:, :], ratio: float) -> ndarray:
    """
    :param gradient: Gradient array (2d)
    :param ratio: Between 0-1
    :return: RGB subarray (1d, has 3 values)
    """
    if ratio == 1:
        return gradient[-1, :]

    i = int(ratio * len(gradient))
    return gradient[i, :]


class Scale:
    colors: ndarray
    rgb: ndarray

    def __init__(self, scale: list[str], resolution: int = 300):
        self.colors = np.array([RGB.from_hex(s) for s in scale])
        self.rgb = create_gradient(self.colors, resolution)

    def __call__(self, ratio: float) -> RGB:
        """
        :param ratio: Between 0-1
        """
        return RGB(*get_raw(self.rgb, ratio))


if __name__ == '__main__':
    scale = Scale(['#232323', '#4F1879', '#B43A78', '#F98766', '#FCFAC0'])

    colors = 100
    for i in range(colors + 1):
        print(scale(i / colors).to_ansi_rgb(False), end=' ')
