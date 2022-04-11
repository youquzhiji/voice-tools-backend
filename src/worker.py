import asyncio
import json
import os
import traceback

import websockets
from hypy_utils.serializer import pickle_decode, pickle_encode
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import WebSocketClientProtocol

from utils.models import Task
from utils.utils import get_worker_info


coordinator_host = os.environ['COORDINATOR_HOST']
worker_info = get_worker_info()


async def start():
    print(f'Connecting to ws://{coordinator_host}')
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
            if isinstance(msg, str):
                if msg != '1':
                    print(f'Unknown message received: {msg}')
                continue

            msg = pickle_decode(msg)

            # Event TODO: Event handlers
            if msg['type'] == 'event':
                print(f'> Received event {msg["event_type"]}')

            # Compute command
            elif msg['type'] == 'compute':
                print(f'> Received compute request.')
                task: Task = msg['task']
                print(task.fn)
                result = task.run()
                await ws.send(json.dumps({'id': task.id, 'result': result}))

            else:
                print(f'> Received unknown message: {msg}')


if __name__ == '__main__':
    while True:
        try:
            asyncio.run(start())
        except Exception as e:
            traceback.print_exc()
            print(f'[-] Connection closed, reconnecting... ({str(e)})')
            continue
