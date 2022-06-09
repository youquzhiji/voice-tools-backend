from __future__ import annotations

import io
import sys
from pathlib import Path

import sgs
from hyfetch.color_util import RGB

import PIL.Image
import matplotlib.pyplot as plt
import numpy as np
import parselmouth
import scipy.io.wavfile
import tensorflow_io as tfio
from hypy_utils import Timer
from inaSpeechSegmenter.constants import ResultFrame
from inaSpeechSegmenter.features import to_wav
from inaSpeechSegmenter.sidekit_mfcc import read_wav
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numba import njit
from numpy import ndarray

from bot.color_scale import get_raw, create_gradient_hex


def draw_ml(file: str, result: list[ResultFrame]) -> io.BytesIO:
    """
    Draw segmentation result

    :param file: Audio file
    :param result: Segmentation result
    :return: Result image in bytes (please close it after use)
    """
    def wav_callback(wavfile: Path):
        sample_rate, audio = scipy.io.wavfile.read(wavfile)
        _time = np.linspace(0, len(audio) / sample_rate, num=len(audio))

        fig: Figure = plt.gcf()
        ax: Axes = plt.gca()

        # Plot audio
        plt.plot(_time, audio, color='white')

        # Set size
        # fig.set_dpi(400)
        fig.set_size_inches(18, 6)

        # Cutoff frequency so that the plot looks centered
        cutoff = min(abs(min(audio)), abs(max(audio)))
        ax.set_ylim([-cutoff, cutoff])
        ax.set_xlim([result[0].start, result[-1].end])

        # Draw segmentation areas
        colors = {'female': '#F5A9B8', 'male': '#5BCEFA', 'default': 'gray'}
        for r in result:
            color = colors[r.label] if r.label in colors else colors['default']
            ax.axvspan(r.start, r.end - 0.01, alpha=.5, color=color)

        # Savefig to bytes
        buf = io.BytesIO()
        plt.axis('off')
        plt.savefig(buf, bbox_inches='tight', pad_inches=0, transparent=False)
        buf.seek(0)
        plt.clf()
        plt.close()
        return buf

    return to_wav(file, tmp_callback=wav_callback)


@njit(cache=True)
def draw_mspect_image(spec: ndarray, gradient: ndarray) -> ndarray:
    """
    Draw mel spectrogram to a ndarray
    """
    w, spec_h = spec.shape
    h = 400

    # Create image
    img = np.zeros((h, w, 3), dtype='uint8')

    # Value bounds
    v_min, v_max = np.min(spec), np.max(spec)
    v_range = v_max - v_min

    # Draw each pixel
    y_conversion = spec_h / h
    for x in range(len(spec)):
        for y in range(h):
            value = spec[x, int(y * y_conversion)]

            # Draw
            img[h - y - 1, x, :] = get_raw(gradient, float((value - v_min) / v_range))

    return img


@njit(cache=True)
def hz_to_mel(hz: float | ndarray) -> float:
    return 2595 * np.log10(1 + hz / 700)


@njit(cache=True)
def draw_spect_line(img: ndarray, line: ndarray, color: ndarray):
    h, w, _ = img.shape
    x_len = len(line) / w

    # Mel mapping
    max_mel = hz_to_mel(8000)
    line = h - hz_to_mel(line) / max_mel * h

    for x in range(w):
        start = int(x_len * x)
        end = int(np.ceil(x_len * (x + 1)))
        window_mean = np.nanmean(line[start:end])

        if np.isnan(window_mean):
            continue

        # Fill 3x3 in + shape
        for dx in [-1, 0, 1]:
            img[int(window_mean) + dx, x, :] = color
            img[int(window_mean), x + dx, :] = color


def draw_mspect(spec: ndarray, freq_array: ndarray, sr: int):
    timer = Timer()

    # Color Gradient
    gradient = create_gradient_hex(['#232323', '#4F1879', '#B43A78', '#F98766', '#FCFAC0'])

    spec = np.log10(spec + 0.1)
    img = draw_mspect_image(spec, gradient)
    timer.log('Done drawing')

    draw_spect_line(img, freq_array[:, 0], np.array(RGB.from_hex('#64fbff')))
    draw_spect_line(img, freq_array[:, 1], np.array(RGB.from_hex('#7bff4f')))
    draw_spect_line(img, freq_array[:, 2], np.array(RGB.from_hex('#93ffb9')))
    draw_spect_line(img, freq_array[:, 3], np.array(RGB.from_hex('#4ffff9')))

    timer.log('Done drawing line')

    # Create image
    my_img = PIL.Image.fromarray(img)
    return my_img


if __name__ == '__main__':
    # Read file
    y, sr, _ = read_wav(r"Z:\EECS 6414\voice_cnn\VT 150hz baseline example.converted.wav")
    sound = parselmouth.Sound(y, sr)

    t = tfio.audio.spectrogram(y, 2048, 2048, 256)
    mel_spectrogram = tfio.audio.melscale(t, rate=sr, mels=128, fmin=0, fmax=8000)

    result, freq_array = sgs.api.calculate_feature_classification(sound)

    mspec = draw_mspect(mel_spectrogram.numpy(), freq_array, sr)
    mspec.show()

