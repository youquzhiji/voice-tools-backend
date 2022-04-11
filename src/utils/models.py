import re
from dataclasses import dataclass
from typing import Callable

from fastapi import WebSocket

from database.db import Worker

version = 1
TOKEN_RE = re.compile(r'^[A-Z0-9]{2048}$')
UUID_RE = re.compile('[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12}', re.I)


@dataclass()
class WorkerInfo:
    token: str
    version: int
    cpu_count: int

    platform: str
    os: str
    cpu: any


@dataclass()
class ConnectedWorker:
    worker: WorkerInfo
    db: Worker
    ws: WebSocket

    # Maximum simultaneous tasks that this worker can handle
    max_tasks: int


@dataclass()
class Task:
    id: str
    fn: Callable
    params: dict

    def run(self):
        return self.fn(**self.params)
