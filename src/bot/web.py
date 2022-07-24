import json
from threading import Thread

import psutil as psutil
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from hypy_utils import Timer
from starlette.requests import Request

from bot import consts
from bot.utils import PrettyJSONResponse
from tasks import compute_audio

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


@app.get('/', response_class=PrettyJSONResponse)
async def status():
    return {
        "What's this page?": "Telegram @voice_tools_bot backend status",
        'version': consts.VERSION,
        'ram': psutil.virtual_memory().percent,
        'cpu': psutil.cpu_percent(),
        'load': psutil.getloadavg(),
        'cat': 'Meow~',
    }


@app.post('/process')
async def process(file: UploadFile, req: Request, with_mel_spect: bool = False):
    timer = Timer()
    timer.log(f'User request received from {req.client.host}')

    return compute_audio(await file.read(), file.filename, with_mel_spect)


def start():
    uvicorn.run(app, port=48257, host="127.0.0.1")


def start_async() -> Thread:
    t = Thread(target=start)
    t.start()
    return t


if __name__ == '__main__':
    start()
