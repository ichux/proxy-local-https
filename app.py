import json
from pathlib import Path

import aiohttp
from aiohttp.client_exceptions import ClientError, ClientOSError

from logs import JobLog

logger = JobLog.make_logger(Path(__file__).with_name("config.json"))


async def read_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


async def es(_id, data):
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=0), trust_env=True
    ) as session:
        try:
            async with session.put(
                f"https://127.0.0.1:9200/csdp/_doc/{_id}",
                json=data,
                auth=aiohttp.BasicAuth("admin", "admin"),
                ssl=False,
            ):
                return
        except (ClientError, ClientOSError):
            return


async def app(scope, receive, send):
    assert scope["type"] == "http"
    assert scope["method"] == "POST"

    body = json.loads(await read_body(receive))
    await es(body.pop("id"), body)

    await send(
        {
            "type": "http.response.start",
            "status": 201,
            "headers": [
                [b"content-type", b"text/plain"],
            ],
        }
    )

    await send(
        {
            "type": "http.response.body",
            "body": b"",
        }
    )
