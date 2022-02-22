from fastapi import FastAPI, WebSocket
from tortoise.contrib.fastapi import register_tortoise

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
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Message text was: {data}")


# Register Tortoise Database
register_tortoise(
    app,
    db_url=db_url,
    modules={'models': ['db']},
    generate_schemas=True,
    add_exception_handlers=True
)
