import base64
import datetime
import json
from pathlib import Path
from typing import NamedTuple

import numpy as np
import parselmouth
import sgs
import tensorflow as tf
import tensorflow_io as tfio
from hypy_utils import Timer
from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.constants import ina_config
from inaSpeechSegmenter.features import to_wav
from inaSpeechSegmenter.sidekit_mfcc import read_wav
from sgs.config import sgs_config

from bot.bdict_encoder import bdict_encode

gpu_devices = tf.config.experimental.list_physical_devices('GPU')
for device in gpu_devices:
    tf.config.experimental.set_memory_growth(device, True)

seg = Segmenter()
np.seterr(invalid='ignore')
sgs_config.time_step = 0.01


def b64(nd: np.ndarray) -> dict[str, any]:
    return {'bytes': base64.b64encode(nd.tobytes()).decode(), 'shape': nd.shape}


class RawComputeResults(NamedTuple):
    result: dict
    freq_array: np.ndarray
    ml: list
    mel_spectrogram: np.ndarray
    sr: int
    audio_dur: float

    def to_json_dict(self) -> dict:
        return {'result': self.result, 'ml': self.ml, 'freq_array': b64(self.freq_array.T),
                'spec': b64(self.mel_spectrogram), 'spec_sr': self.sr}

    def to_bdict(self) -> bytes:
        j = {'result': self.result, 'ml': self.ml, 'spec_sr': self.sr,
             'spec_rows': self.mel_spectrogram.shape[0], 'audio_dur': self.audio_dur}
        bd = {'freq_array': self.freq_array.T.tobytes(), 'spec': self.mel_spectrogram.tobytes(),
              'json': json.dumps(j)}
        return bdict_encode(bd)


def write_file(file: bytes, file_name: str) -> Path:
    """
    Write bytes
    """
    tmp_file = Path(datetime.datetime.now().strftime(f'%Y-%m-%d %H-%M-%S {Path(file_name).suffix}'))
    tmp_file = Path(f'audio_tmp/{tmp_file}')
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(file)

    return tmp_file


def compute_audio_raw(file: Path) -> RawComputeResults:
    """
    Compute user request

    :param file: Audio file
    :return: Computation result
    """
    timer = Timer()

    # Read file
    wav_full = to_wav(file, sr=None)
    y, sr, _ = read_wav(wav_full)
    sound = parselmouth.Sound(y, sr)
    timer.log('File read.')

    # Calculate features
    try:
        result, freq_array = sgs.api.calculate_feature_classification(sound)
        result = {k: {x: result[k][x] for x in result[k] if not np.isnan(result[k][x])} for k in result}
        timer.log('Features calculated')
    except IndexError as e:
        # If the audio is too short, an IndexError: index -1 is out of bounds for axis 0 with size 0 will be raised
        result = {}
        freq_array = np.ndarray((0, 4), 'float32')
        timer.log(f'Features calculation failed - IndexError: {e}')

    # Calculate ML
    ina_config.auto_convert = sr != 16000
    try:
        ml = seg(wav_full)
        timer.log('ML Segmented')
    except KeyError as e:
        # If the audio is too short, a KeyError: 'pop from an empty set' might be raised
        ml = []
        timer.log(f'ML Segment Failed - KeyError: {e}')

    # Calculate mel spectrogram
    t = tfio.audio.spectrogram(y, 2048, 2048, 512)
    mel_spectrogram = tfio.audio.melscale(t, rate=sr, mels=128, fmin=0, fmax=8000).numpy()

    return RawComputeResults(result, freq_array, ml, mel_spectrogram, sr, sound.duration)


def compute_audio(file: bytes, file_name: str) -> dict:
    return compute_audio_raw(write_file(file, file_name)).to_json_dict()
