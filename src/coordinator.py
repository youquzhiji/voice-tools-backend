from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

app = FastAPI()


@app.get('/')
async def root():
    return {'message': 'Hello World'}


# Register Tortoise Database
register_tortoise(
    app,
    db_url='mysql://pwp:qwq@localhost:3306/test',
    modules={'models': ['db']},
    generate_schemas=True,
    add_exception_handlers=True
)
