import numpy as np
from hyfetch.color_util import RGB
from numpy import ndarray


def get_color_with_ratio(c1: int, c2: int, ratio: float) -> int:
    return round(c2 * ratio + c1 * (1 - ratio))


class Scale:
    colors: list[RGB]
    rgb: ndarray

    def __init__(self, scale: list[str], resolution: int = 500):
        self.colors = [RGB.from_hex(s) for s in scale]
        res = resolution * len(self.colors) - 1

        result = []

        # Create gradient mapping
        for i in range(len(self.colors) - 1):
            c1 = self.colors[i]
            c2 = self.colors[i + 1]

            for r in range(resolution):
                ratio = r / resolution

                r = get_color_with_ratio(c1.r, c2.r, ratio)
                g = get_color_with_ratio(c1.g, c2.g, ratio)
                b = get_color_with_ratio(c1.b, c2.b, ratio)

                result.append(RGB(r, g, b))

        # Convert to 2D array
        nd = np.zeros((len(result), 3), dtype='uint8')
        for i, r in enumerate(result):
            nd[i, :] = r

        self.rgb = nd

    def __call__(self, ratio: float) -> RGB:
        """
        :param ratio: Between 0-1
        """
        if ratio == 1:
            return self.colors[-1]

        i = int(ratio * len(self.rgb))
        return RGB(*self.rgb[i, :])


if __name__ == '__main__':
    scale = Scale(['#232323', '#4F1879', '#B43A78', '#F98766', '#FCFAC0'])
    for i in range(11):
        print(scale(i / 10).to_ansi_rgb(False) + ' ')
