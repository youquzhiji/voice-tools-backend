import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from hypy_utils import Timer
from starlette.requests import Request

from tasks import compute

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


@app.post('/process')
async def process(file: UploadFile, req: Request, with_mel_spect: bool = False):
    timer = Timer()
    timer.log('User request received.')

    tmp_file = Path(datetime.datetime.now().strftime(f'%Y-%m-%d %H-%M-%S {req.client.host.replace(":", "")}{Path(file.filename).suffix}'))
    tmp_file = Path(f'temp/{tmp_file}')
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_bytes(await file.read())

    timer.log('> File Downloaded')

    return compute(tmp_file, with_mel_spect)
