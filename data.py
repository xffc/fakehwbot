import aiosqlite, requests
from config import HEADERS, REQ_PROXIES
from secrets import token_urlsafe
from dataclasses import dataclass
from cachetools import TTLCache
from typing import Optional, Any

database: aiosqlite.Connection

@dataclass
class Subscription:
    link: str
    headers: str
    
    # FORMAT: LINK_LENGTH, HEADERS_LENGTH, LINK_STR, HEADERS_STR
    def as_bytes(self) -> bytes:
        length_as_bytes = len(self.link).to_bytes() + len(self.headers).to_bytes()
        data = (self.link + self.headers).encode()
        return length_as_bytes + data
    
    def send_request(self) -> requests.Response:
        return requests.get(self.link, headers=HEADERS[self.headers], proxies=REQ_PROXIES)
    
    def __str__(self) -> str:
        return f"{self.link} ({self.headers})"
    
    @classmethod
    def from_bytes(cls, data: bytes) -> list[Subscription]:
        subs: list[Subscription] = []
        index = 0
        
        while index < len(data):
            link_length = data[index]
            index += 1
            headers_length = data[index]
            index += 1
            
            link = data[index:index+link_length].decode()
            index += link_length
            headers = data[index:index+headers_length].decode()
            index += headers_length
            
            subs.append(Subscription(link, headers))
            
        return subs

_user_cache: TTLCache[Any, User] = TTLCache(maxsize=2000, ttl=300)
@dataclass
class User:
    uid: int
    subscriptions: list[Subscription]
    token: str
    
    def pack_subs(self) -> bytes:
        array = bytes()
        for sub in self.subscriptions:
            array += sub.as_bytes()
        return array
    
    async def save(self):
        await database.execute("UPDATE users SET subscriptions = ? WHERE uid = ?", (self.pack_subs(), self.uid,))
        await database.commit()
    
    @classmethod
    async def fetch(cls, uid: int) -> Optional[User]:
        if uid in _user_cache:
            return _user_cache[uid]
        
        cursor = await database.execute("SELECT subscriptions, token FROM users WHERE uid = ?", (uid,))
        row = await cursor.fetchone()
        if row == None:
            return None
        
        user = User(uid, Subscription.from_bytes(row[0]), row[1])
        return user
    
    @classmethod
    async def token_fetch(cls, token: str) -> Optional[User]:
        if token in _user_cache:
            return _user_cache[token]
        
        cursor = await database.execute("SELECT uid, subscriptions FROM users WHERE token = ?", (token,))
        row = await cursor.fetchone()
        if row == None:
            return None
        
        user = User(row[0], Subscription.from_bytes(row[1]), token)
        return user
        
    @classmethod
    async def create(cls, uid: int) -> User:
        user = User(uid, [], token_urlsafe(64))
        await database.execute("INSERT INTO users VALUES (?, ?, ?)", (uid, user.pack_subs(), user.token))
        await database.commit()
        return user

async def get_user(uid: int) -> User:
    user = await User.fetch(uid)
    if user == None:
        user = await User.create(uid)
    return user

async def get_tokenuser(token: str) -> Optional[User]:
    return await User.token_fetch(token)

async def connect_database():
    global database
    database = await aiosqlite.connect("users.db")
    await database.execute("CREATE TABLE IF NOT EXISTS users (uid INTEGER PRIMARY KEY NOT NULL, subscriptions BLOB NOT NULL, token VARCHAR(64) NOT NULL)")