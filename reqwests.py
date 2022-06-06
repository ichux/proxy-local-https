import asyncio
import ssl
from datetime import datetime
from pathlib import Path

import aiohttp
import requests

URL: str = "https://localhost:8000/"
SSL_CERT = Path(__file__).parent / "ssl/client.pem"
SSL_CTX = ssl.create_default_context()
SSL_CTX.load_verify_locations(SSL_CERT)


def post_sync(data):
    response = requests.post(URL, json=data, verify=(SSL_CERT))
    return response


async def post_async(data):
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=0), trust_env=True
    ) as session:
        async with session.post(
            URL,
            json=data,
            ssl=False,
        ) as response:
            return response


async def main():
    payloads = [
        {
            "id": _,
            "emitter": f"emitter.fake{_}",
            "log": "INFO",
            "datetime": str(datetime.now()),
        }
        for _ in range(10)
    ]
    for payload in payloads:
        sync_res = post_sync(payload)
        async_res = await post_async(payload)
        print((sync_res.status_code, async_res.status))


if __name__ == "__main__":
    asyncio.run(main())
