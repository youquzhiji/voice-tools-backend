import datetime
from multiprocessing import Process
from pathlib import Path

import uvicorn
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


def start():
    uvicorn.run(app, port=48257, host="127.0.0.1")


def start_async() -> Process:
    p = Process(target=start)
    p.start()
    return p


if __name__ == '__main__':
    start()
