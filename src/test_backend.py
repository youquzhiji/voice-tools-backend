import base64
import datetime
from math import isnan
from pathlib import Path

import numpy as np
import parselmouth
import sgs
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from inaSpeechSegmenter import Segmenter
from starlette.requests import Request

from server.utils import Timer

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


seg = Segmenter()
np.seterr(invalid='ignore')


@app.post('/process')
async def process(file: UploadFile, req: Request):
    timer = Timer()

    # Download file to a temporary location
    # TODO: Is this safe?
    timer.log('Received file.')
    tmp_file = Path(datetime.datetime.now().strftime(f'%Y-%m-%d %H-%M-%S {req.client.host.replace(":", "")}{Path(file.filename).suffix}'))
    tmp_file = Path(f'temp/{tmp_file}')
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(await file.read())

    timer.log('Downloaded.')

    # Read file
    sound = parselmouth.Sound(str(tmp_file.absolute()))
    timer.log('File read.')

    # Calculate features
    result, freq_array = sgs.api.calculate_feature_classification(sound)
    timer.log('Features calculated')
    result = {k: {x: result[k][x] for x in result[k] if not isnan(result[k][x])} for k in result}
    freq_array = freq_array.T
    freq_array_bytes = base64.b64encode(freq_array.tobytes())

    # Calculate ML
    ml = seg(str(tmp_file.absolute()))
    timer.log('ML Segmented')

    return {'filename': file.filename, 'result': result, 'ml': ml,
            'freq_array': {'bytes': freq_array_bytes, 'shape': freq_array.shape}}


if __name__ == '__main__':
    # print(sgs.api._calculate_fem_prob('pitch', 120))
    # r, freq_array = sgs.api.calculate_feature_classification(parselmouth.Sound('Z:/EECS 6414/voice_cnn/VT 150hz baseline example.mp3'))
    r, freq_array = sgs.api.calculate_feature_classification(parselmouth.Sound('C:/Workspace/EECS 6414 Backup/SpeechGenderAnalysis/test.wav'))
    print(r)
    print(freq_array.dtype)
    print(freq_array.tolist())
    print(freq_array.tobytes())
    percentage = sum(r['fem_prob'].values()) / len(r['fem_prob'])
    print(percentage)
