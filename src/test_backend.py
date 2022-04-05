import base64
import datetime
from math import isnan
from pathlib import Path

import numpy as np
import parselmouth
import sgs
import tensorflow as tf
import tensorflow_io as tfio
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from inaSpeechSegmenter import Segmenter
from inaSpeechSegmenter.constants import ina_config
from inaSpeechSegmenter.features import to_wav
from inaSpeechSegmenter.sidekit_mfcc import read_wav
from sgs.config import sgs_config
from starlette.requests import Request
from tensorflow import config

from server.utils import Timer

gpu_devices = tf.config.experimental.list_physical_devices('GPU')
for device in gpu_devices:
    tf.config.experimental.set_memory_growth(device, True)

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


seg = Segmenter()
np.seterr(invalid='ignore')
sgs_config.time_step = 0.032


def b64(nd: np.ndarray) -> dict[str, any]:
    return {'bytes': base64.b64encode(nd.tobytes()), 'shape': nd.shape}


@app.post('/process')
async def process(file: UploadFile, req: Request, with_mel_spect: bool = False):
    timer = Timer()

    # Download file to a temporary location
    tmp_file = Path(datetime.datetime.now().strftime(f'%Y-%m-%d %H-%M-%S {req.client.host.replace(":", "")}{Path(file.filename).suffix}'))
    tmp_file = Path(f'temp/{tmp_file}')
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(await file.read())
    timer.log('Downloaded.')

    # Read file
    wav_full = to_wav(tmp_file, sr=None)
    y, sr, _ = read_wav(wav_full)
    sound = parselmouth.Sound(str(wav_full))
    timer.log('File read.')

    # Calculate features
    try:
        result, freq_array = sgs.api.calculate_feature_classification(sound)
        result = {k: {x: result[k][x] for x in result[k] if not isnan(result[k][x])} for k in result}
        timer.log('Features calculated')
    except IndexError as e:
        # If the audio is too short, an IndexError: index -1 is out of bounds for axis 0 with size 0 will be raised
        result = {}
        freq_array = np.array([])
        timer.log(f'Features calculation failed - IndexError: {e}')

    # Calculate ML
    ina_config.auto_convert = sound.sampling_frequency != 16000
    try:
        ml = seg(wav_full)
        timer.log('ML Segmented')
    except KeyError as e:
        # If the audio is too short, a KeyError: 'pop from an empty set' might be raised
        ml = []
        timer.log(f'ML Segment Failed - KeyError: {e}')

    data = {'filename': file.filename, 'result': result, 'ml': ml,
            'freq_array': b64(freq_array.T)}

    # Calculate mel spectrogram (if needed)
    if with_mel_spect:
        t = tfio.audio.spectrogram(y, 2048, 2048, 512)
        mel_spectrogram = tfio.audio.melscale(t, rate=sr, mels=128, fmin=0, fmax=8000)
        data['spec'] = b64(mel_spectrogram.numpy())
        data['spec_sr'] = sr

    return data
