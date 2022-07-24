from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from uuid import uuid4

import psutil as psutil
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from hypy_utils import Timer
from starlette.requests import Request

from bot import consts
from bot.utils import PrettyJSONResponse
from tasks import compute_audio


SAVED_RESULTS_PATH = Path('audio_results')

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


@app.get('/results')
async def get_process_results(uuid: str) -> dict | None:
    """
    Get results from a previously saved UUID.

    :param uuid:
    :return: Results dict or None if not found
    """
    path = (SAVED_RESULTS_PATH / f'{uuid}.json')
    if not path.is_file():
        return None
    return json.loads(path.read_text('utf-8'))


async def save_process_results(results: dict) -> str:
    """
    Save results and return a UUID for getting results later.

    :param results: Results
    :return: UUID
    """
    # TODO: Use redis / mysql
    uuid = str(uuid4())
    (SAVED_RESULTS_PATH / f'{uuid}.json').write_text(json.dumps(results), 'utf-8')
    return uuid


def start():
    uvicorn.run(app, port=48257, host="127.0.0.1")


def start_async() -> Thread:
    t = Thread(target=start)
    t.start()
    return t


if __name__ == '__main__':
    start()