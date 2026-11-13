API_ENABLED: bool = False
API_HOST: str = "0.0.0.0"
API_PORT: int = 8888
API_ROOT_PATH: str = "" # example: /fakehwbot
API_DISPLAY: str = "https://example.com"

THRONE_VER: str = "1.3.2"
HAPP_VER: str = "4.7.2/2610301207508"
INCY_VER: str = "3.9.0"

HEADERS: dict[str, dict[str, str]] = {
    "singbox": {
        "x-hwid": "47f2bcf41664b5dc",
        "x-device-os": "Android",
        "x-ver-os": "16",
        "x-device-model": "motorola edge 70 max",
        "User-Agent": f"Throne/{THRONE_VER}"
    },
    "happ": {
        "X-Device-Os": "Windows",
        "X-Device-Model": "DESKTOP-DODE6BL_x86_64",
        "X-Hwid": "0b0d3622-64a0-4301-aa7a-7fae4c944733",
        "X-Ver-Os": "11_10.0.26100",
        "X-Device-Locale": "RU",
        "User-Agent": f"Happ/{HAPP_VER.split("/")[0]}/Windows/{HAPP_VER.split("/")[1]}",
        "X-App-Version": HAPP_VER.split("/")[0]
    },
    "incy": {
        "user-Agent": f"INCY/{INCY_VER}/windows 11 Dalvik/21.0.12+8-LTS",
        "x-app-version": INCY_VER,
        "x-device-locale": "en_US",
        "x-client": "INCY",
        "x-hwid": "3F44988F-2F17-9150-E6DE-6C033886C054",
        "x-device-os": "Windows 11",
        "x-ver-os": "10.0",
        "x-device-model": "Windows 11 amd64"
    }
}

TOKEN: str = "TELEGRAM_BOT_TOKEN"

BOT_PROXY: str | None = None # example: "http://127.0.0.1:10808"

REQ_PROXIES: str | None = None # example: "http://127.0.0.1:10808"
