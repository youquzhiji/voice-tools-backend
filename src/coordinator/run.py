import asyncio
import json
import re
import time
import traceback
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
class ConnectedServer:
    host: str
    token: str
    server: Server
    ws: WebSocket


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
    return [{'host': s.host} for s in pool.get_connected()]


@app.websocket('/ws/server-connect')
async def server_connect(ws: WebSocket):
    await ws.accept()

    # Validate server info
    try:
        server_info = json.loads(await ws.receive_text())
        host = ws.client.host

        print(f'WS: Server {host} connected, validating')

        # Check version
        if int(server_info['version']) != version:
            print('> [-] Version mismatch, closing')
            await ws.send_text(f'Please upgrade your server to the latest version {version} '
                               f'(You\'re on {server_info["version"]})')
            return

        # Check token registration
        token = server_info['token']
        if not re.compile(r'^[A-Z0-9]{2048}$').match(token):
            print('> [-] Token format mismatch')
            await ws.send_text('Your server token is in the wrong format (must be 2048 bit string)')
            return
        server, created = await Server.get_or_create(token=token)
        if created:
            print(f'> [U] Token created ({token[:16]}...)')
        if not server.approved:
            print('> [-] Token not approved')
            await ws.send_text('Your server token is not approved')
            return

        if not server.nickname:
            server.nickname = token[16:]

        # Passed, add to server pool
        print('> [+] Validation passed.')
        await ws.send_text('Success')
        pool.pool.append(ConnectedServer(host, token, server, ws))

    # Any other errors
    except Exception as e:
        print(f'> [-] Error: {str(e)}')
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
