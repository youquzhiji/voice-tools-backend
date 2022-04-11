import asyncio
import json
import os

import websockets
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import WebSocketClientProtocol

from utils.utils import get_worker_info


coordinator_host = os.environ['COORDINATOR_HOST']
worker_info = get_worker_info()


async def start():
    async with websockets.connect(f'ws://{coordinator_host}/ws/worker-connect') as ws:
        ws: WebSocketClientProtocol

        # Send worker information
        await ws.send(json.dumps(worker_info))

        # Receive validation results
        validation = await ws.recv()
        if validation.strip() != 'Success':
            raise ConnectionError(validation)
        print('[+] Connected, start polling')

        # Start receiving messages, they must be json format
        while True:
            msg = await ws.recv()

            # Ping
            if msg == '1':
                continue

            msg = json.loads(msg)

            # Event TODO: Event handlers
            if msg['type'] == 'event':
                print(f'> Received event {msg["event_type"]}')

            # Compute command
            elif msg['type'] == 'compute':
                print(f'> Received compute request: {msg}')
                # if msg['compute_type'] == 'pi'

            else:
                print(f'> Received unknown message: {msg}')

            await ws.send(json.dumps({'success': True}))


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(start())
        except (ConnectionClosedError, TimeoutError) as e:
            print(f'[-] Connection closed, reconnecting... ({str(e)})')
            continue
