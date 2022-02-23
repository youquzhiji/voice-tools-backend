import asyncio
import json
import re
import uuid
from dataclasses import dataclass
from functools import reduce
from typing import Callable

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketState
from tortoise.contrib.fastapi import register_tortoise
from websockets.exceptions import ConnectionClosedError

from constants import version
from coordinator.db import Server

db_url = 'mysql://pwp:qwq@localhost:3306/6414'
app = FastAPI()


@dataclass()
class ServerInfo:
    token: str
    version: int
    cpu_count: int
    benchmark: int

    platform: str
    os: str
    cpu: any


@dataclass()
class ConnectedServer:
    server: ServerInfo
    db: Server
    ws: WebSocket

    # Maximum simultaneous tasks that this server can handle
    max_tasks: int


@dataclass()
class Task:
    id: str
    task: str
    params: any
    callback: Callable


class ServerPool:
    """This class controls server pools and keeps information about each server"""
    pool: list[ConnectedServer] = []
    completed_tasks = []
    running_tasks: dict[str, tuple[Task, ConnectedServer]] = {}
    queued_tasks: list[Task] = []

    def remove_disconnected(self) -> None:
        to_remove = [s for s in self.pool if s.ws.client_state == WebSocketState.DISCONNECTED]
        for s in to_remove:
            self.pool.remove(s)

    def get_connected(self) -> list[ConnectedServer]:
        self.remove_disconnected()
        return self.pool

    def get_resting_servers(self) -> list[ConnectedServer]:
        """Get servers that are not doing anything. If a server has a max_tasks of 6 and is resting,
        then the server will appear in the result 6 times.
        """
        active = [s[1] for s in self.running_tasks.values()]
        resting = [[s] * (s.max_tasks - active.count(s)) for s in self.get_connected()]
        return reduce(list.__add__, resting) if resting else []

    async def check_queue(self):
        """Check if any tasks in queue can be started"""
        resting = self.get_resting_servers()

        # Run tasks
        while len(resting) > 0 and len(self.queued_tasks) > 0:
            s = resting.pop(0)
            t = self.queued_tasks.pop(0)

            # Run and add to running list
            await s.ws.send_json({'type': 'compute', 'id': t.id, 'task': t.task, 'params': t.params})
            self.running_tasks[t.id] = (t, s)

    async def run_compute(self, task: str, params, callback: Callable) -> None:
        """Enqueue a computation task"""
        id = str(uuid.uuid4())
        self.queued_tasks.append(Task(id, task, params, callback))
        await self.check_queue()

    async def add_server(self, server: ConnectedServer):
        """Listen to server finishing requests"""
        self.pool.append(server)

        async def listen():
            try:
                while server.ws.client_state == WebSocketState.CONNECTED:
                    text = await server.ws.receive_text()
                    print(text)
            except ConnectionClosedError:
                print(f'> [-] {server.ws.client.host} Connection closed')
                return

        await asyncio.gather(listen())


pool = ServerPool()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/test')
async def endpoint_test():
    await pool.run_compute('pi', 1000, print)


@app.get('/pool')
async def active_servers():
    return [{'host': s.ws.client.host} for s in pool.get_connected()]


@app.websocket('/ws/server-connect')
async def server_connect(ws: WebSocket):
    await ws.accept()

    # Validate server info
    try:
        info = ServerInfo(**json.loads(await ws.receive_text()))
        print(f'WS: Server {ws.client.host} connected, validating')

        # Check version
        assert info.version == version,\
            f'Please upgrade to the latest version {version} (You\'re on {info.version})'

        # Check token registration
        assert re.compile(r'^[A-Z0-9]{2048}$').match(info.token), 'Token format mismatch'
        server, created = await Server.get_or_create(token=info.token)
        if created:
            print(f'> [U] Token created ({info.token[:16]}...)')
        assert server.approved, 'Token not approved'

        if not server.nickname:
            server.nickname = info.token[16:]

        # Check max tasks
        max_tasks = min(info.cpu_count, 8)

        # Passed, add to server pool
        print('> [+] Validation passed.')
        await ws.send_text('Success')
        await pool.add_server(ConnectedServer(info, server, ws, max_tasks))

    # Any other errors
    except Exception as e:
        print(f'> [-] {str(e)}')
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_text(f'Error: {str(e)}')
        return


# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['coordinator.db']},
    generate_schemas=True,
    add_exception_handlers=True
)
