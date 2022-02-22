import asyncio
import json

import websockets
from websockets.legacy.client import WebSocketClientProtocol

from constants import coordinator_host
from server.utils import get_server_info


async def start():
    async with websockets.connect(f'ws://{coordinator_host}/ws/server-connect') as ws:
        ws: WebSocketClientProtocol

        # Send server information
        await ws.send(json.dumps(get_server_info()))

        # Receive validation results
        print(await ws.recv())


if __name__ == '__main__':
    asyncio.run(start())
