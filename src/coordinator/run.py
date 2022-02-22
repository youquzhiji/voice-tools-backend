import asyncio
import json
import re
import traceback

from fastapi import FastAPI, WebSocket
from tortoise.contrib.fastapi import register_tortoise

from constants import version
from coordinator.db import Server

db_url = 'mysql://pwp:qwq@localhost:3306/6414'
app = FastAPI()
server_pool: list[WebSocket] = []


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/test')
async def endpoint_test():
    # Get unclosed servers
    return ''


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

        # Passed, add to server pool
        print('> [+] Validation passed.')
        await ws.send_text('Success')
        server_pool.append(ws)

    except Exception as e:
        print(f'> [-] Error: {str(e)}')
        await ws.send_text(f'Error: {str(e)}')
        return

    while True:
        await asyncio.sleep(60)
        await ws.send_json({'type': 'event', 'event_type': 'ping'})


# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['coordinator.db']},
    generate_schemas=True,
    add_exception_handlers=True
)
