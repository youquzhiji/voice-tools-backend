import asyncio
import copy
import json
import os
import re
import traceback
import uuid
from functools import reduce
from typing import Callable

from fastapi import FastAPI, WebSocket, UploadFile
from hypy_utils.serializer import pickle_encode
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.websockets import WebSocketState
from tortoise.contrib.fastapi import register_tortoise
from websockets.exceptions import ConnectionClosedError

from utils.models import version, ConnectedWorker, Task, WorkerInfo
from database.db import Worker
from tasks import compute_audio

db_url = os.environ['MYSQL_URL']
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)


class WorkerPool:
    """This class controls worker pools and keeps information about each worker"""
    pool: list[ConnectedWorker] = []
    completed_tasks = []
    running_tasks: dict[str, tuple[Task, ConnectedWorker]] = {}
    queued_tasks: list[Task] = []

    def remove_disconnected(self) -> None:
        """Remove disconnected workers"""
        to_remove = [s for s in self.pool if s.ws.client_state != WebSocketState.CONNECTED]
        for s in to_remove:
            self.pool.remove(s)

    def get_connected(self) -> list[ConnectedWorker]:
        """Get connected workers"""
        self.remove_disconnected()
        return self.pool

    def get_resting_workers(self) -> list[ConnectedWorker]:
        """Get workers that are not doing anything. If a worker has a max_tasks of 6 and is resting,
        then the worker will appear in the result 6 times.
        """
        active = [s[1] for s in self.running_tasks.values()]
        resting = [[s] * (s.max_tasks - active.count(s)) for s in self.get_connected()]
        return reduce(list.__add__, resting) if resting else []

    async def check_queue(self):
        """Check if any tasks in queue can be started"""
        resting = self.get_resting_workers()

        # Run tasks
        while len(resting) > 0 and len(self.queued_tasks) > 0:
            s = resting.pop(0)
            t = self.queued_tasks.pop(0)

            # Run and add to running list
            await s.ws.send_bytes(pickle_encode({'type': 'compute', 'task': t}))
            self.running_tasks[t.id] = (t, s)

    async def run_compute(self, task: Callable, params: any, callback: Callable) -> None:
        """Enqueue a computation task"""
        id = str(uuid.uuid4())
        self.queued_tasks.append(Task(id, task, params, callback))
        await self.check_queue()

    async def add_worker(self, worker: ConnectedWorker):
        """Listen to worker finishing requests"""
        self.pool.append(worker)

        async def listen():
            try:
                while worker.ws.client_state == WebSocketState.CONNECTED:
                    text = await worker.ws.receive_text()
                    obj = json.loads(text)
                    id = obj['id']
                    print(f'> [R] Received Response for ID {id}, calling callback')
                    # print(text)
            except ConnectionClosedError:
                print(f'> [-] {worker.ws.client.host} Connection closed')
                return

        await asyncio.gather(listen())


pool = WorkerPool()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post('/process')
async def process(file: UploadFile, req: Request, with_mel_spect: bool = False):
    print(f'Received request from {req.client.host}')
    params = {'file': await file.read(), 'file_name': file.filename, 'with_mel_spect': with_mel_spect}
    await pool.run_compute(compute_audio, params, print)


@app.get('/pool')
async def active_workers():
    def censor(worker: WorkerInfo):
        info = copy.copy(worker)
        info.token = '[Censored]'
        return info

    return [{'host': s.ws.client.host, 'info': censor(s.worker), 'max_tasks': s.max_tasks}
            for s in pool.get_connected()]


@app.websocket('/ws/worker-connect')
async def worker_connect(ws: WebSocket):
    await ws.accept()

    # Validate worker info
    try:
        info = WorkerInfo(**json.loads(await ws.receive_text()))
        print(f'WS: Worker {ws.client.host} connected, validating')

        # Check version
        assert info.version == version,\
            f'Please upgrade to the latest version {version} (You\'re on {info.version})'

        # Check token registration
        assert re.compile(r'^[A-Z0-9]{2048}$').match(info.token), 'Token format mismatch'
        worker, created = await Worker.get_or_create(token=info.token)
        if created:
            print(f'> [U] Token created ({info.token[:16]}...)')
        assert worker.approved, 'Token not approved'

        if not worker.nickname:
            worker.nickname = info.token[16:]

        # Check max tasks
        max_tasks = min(info.cpu_count, 8)

        # Passed, add to worker pool
        print('> [+] Validation passed.')
        await ws.send_text('Success')
        await pool.add_worker(ConnectedWorker(info, worker, ws, max_tasks))

    # Any other errors
    except Exception as e:
        traceback.print_exc()
        print(f'> [-] {str(e)}')
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_text(f'Error: {str(e)}')
        return


# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['database.db']},
    generate_schemas=True,
    add_exception_handlers=True
)
