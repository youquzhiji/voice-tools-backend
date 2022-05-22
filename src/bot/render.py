import io
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy.io.wavfile
from inaSpeechSegmenter.constants import ResultFrame
from inaSpeechSegmenter.features import to_wav
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def draw_ml(file: str, result: list[ResultFrame]):
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
