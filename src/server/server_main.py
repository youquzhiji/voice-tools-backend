import asyncio
import json

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import WebSocketClientProtocol

from constants import coordinator_host
from server.utils import get_server_info


async def start():
    async with websockets.connect(f'ws://{coordinator_host}/ws/server-connect') as ws:
        ws: WebSocketClientProtocol

        # Send server information
        await ws.send(json.dumps(get_server_info()))

        # Receive validation results
        validation = await ws.recv()
        if validation.strip() != 'Success':
            raise ConnectionError(validation)
        print('[+] Connected')

        while True:
            msg = await ws.recv()
            print(f'> Received message: {msg}')
            await ws.send(json.dumps({'success': True}))


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(start())
        except (ConnectionClosedError, TimeoutError) as e:
            print(f'[-] Connection closed, reconnecting... ({str(e)})')
            continue
