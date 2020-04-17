from fastapi import Request


async def get_db(request: Request):
    async with request.app.db.acquire() as con:
        yield con
