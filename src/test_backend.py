import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from hypy_utils import Timer
from starlette.requests import Request

from tasks import compute_audio

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


@app.post('/process')
async def process(file: UploadFile, req: Request, with_mel_spect: bool = False):
    timer = Timer()
    timer.log(f'User request received from {req.client.host}')

    return compute_audio(await file.read(), file.filename, with_mel_spect)
