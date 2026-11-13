from fastapi import FastAPI, HTTPException, status, Response
from data import get_tokenuser
from aiohttp import ClientSession
from config import API_HOST, API_PORT, API_ROOT_PATH
from uvicorn import Config, Server

app = FastAPI(root_path=API_ROOT_PATH)

@app.api_route("/user/{token}/subs")
async def get_user_subs(token: str):
    user = await get_tokenuser(token)
    if user == None:
        raise HTTPException(404, "User not found (invalid token)")
    return user.subscriptions

@app.api_route("/user/{token}/subs/{index}")
async def get_user_sub(token: str, index: int):
    user = await get_tokenuser(token)
    if user == None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found (invalid token)")
    
    index -= 1
    if index < 0 or index + 1 > len(user.subscriptions):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid index")
    sub = user.subscriptions[index]
    try:
        async with ClientSession() as session:
            content = await (await sub.send_request(session)).text()
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST)
    
    return Response(content)

async def start():
    config = Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="INFO"
    )
    server = Server(config)
    await server.serve()