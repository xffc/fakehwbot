# fakehwbot
A Telegram bot with an API (optional) that allows you to renew subscriptions from a single HWID, bypassing device limits.

## Usage
### Telegram
Commands:
1. `/start` - list of subscriptions, export, and help
2. `/add SUB_URL HEADER` - add a subscription (available headers are specified in the config and displayed in /start)
3. `/remove INDEX` - remove a subscription (for the particularly savvy, start with index 1)
4. `/api` – API information, user token

### API
Available endpoints can be found at `/redoc` (on the API itself).

## Installation (self-hosted)
1. Clone the repository
2. Install the packages `aiogram, aiosqlite, cachetools, requests`
   - If you plan to use a proxy for Telegram, install `aiohttp_socks`
   - If you plan to enable the API, additionally install: `fastapi, uvicorn`
3. Modify `config.py` as needed
4. Run `bot.py`

## Technical Details
The database runs via `aiosqlite`.

The API runs on `fastapi` with `uvicorn`.

Each subscription has the format `[LINK_LENGTH, HEADERS_LENGTH, LINK_STR, HEADERS_STR]`; all subscriptions are stored in a BLOB.
