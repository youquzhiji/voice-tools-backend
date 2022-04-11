from dataclasses import dataclass
from typing import Callable

from fastapi import WebSocket

from database.db import Worker

version = 1


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
    callback: Callable

    def run(self):
        return self.fn(**self.params)
