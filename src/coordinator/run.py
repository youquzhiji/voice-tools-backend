import asyncio
import json
import re
from dataclasses import dataclass

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


@dataclass()
class ConnectedServer:
    server: ServerInfo
    db: Server
    ws: WebSocket

    # Maximum simultaneous tasks that this server can handle
    max_tasks: int


class ServerPool:
    """This class controls server pools and keeps information about each server"""
    pool: list[ConnectedServer] = []

    def remove_disconnected(self) -> None:
        to_remove = [s for s in self.pool if s.ws.client_state == WebSocketState.DISCONNECTED]
        for s in to_remove:
            self.pool.remove(s)

    def get_connected(self) -> list[ConnectedServer]:
        self.remove_disconnected()
        return self.pool


pool = ServerPool()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/test')
async def endpoint_test():
    # Get unclosed servers
    target = pool.get_connected()[0].ws
    await target.send_json({'type': 'compute'})
    return await target.receive_text()


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
        pool.pool.append(ConnectedServer(info, server, ws, max_tasks))

    # Any other errors
    except Exception as e:
        print(f'> [-] {str(e)}')
        await ws.send_text(f'Error: {str(e)}')
        return

    # Send ping https://github.com/tiangolo/fastapi/issues/709
    async def ping():
        try:
            while ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text('1')
                await asyncio.sleep(1)
        except ConnectionClosedError:
            print(f'> [-] {server.nickname} Connection closed')
            return

    await asyncio.gather(ping())

# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['coordinator.db']},
    generate_schemas=True,
    add_exception_handlers=True
)
