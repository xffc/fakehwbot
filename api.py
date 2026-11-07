from fastapi import FastAPI, HTTPException, status, Response
from requests import RequestException
from data import get_tokenuser
from config import API_HOST, API_PORT
from uvicorn import Config, Server

app = FastAPI()

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
    
    if index < 0 or index + 1> len(user.subscriptions):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invalid index")
    sub = user.subscriptions[index]
    try:
        content = sub.send_request().content
    except RequestException:
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