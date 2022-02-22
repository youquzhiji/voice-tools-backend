import json
import traceback

from fastapi import FastAPI, WebSocket
from tortoise.contrib.fastapi import register_tortoise

from constants import version

db_url = 'mysql://pwp:qwq@localhost:3306/6414'
app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.get('/lifecycle')
async def lifecycle():
    return {'message': 'To be implemented'}


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
            print('> Version mismatch, closing')
            await ws.send_text(f'Please upgrade your server to the latest version {version} '
                               f'(You\'re on {server_info["version"]})')
            return

        # Passed
        print('> Validation passed.')
        await ws.send_text('Success')

    except Exception as e:
        print(f'> Error: {str(e)}')
        await ws.send_text(f'Error: {str(e)}')
        return

    # while True:
    #     data = await ws.receive_text()
    #     await ws.send_text(f"Message text was: {data}")


# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['coordinator.db']},
    generate_schemas=True,
    add_exception_handlers=True
)
