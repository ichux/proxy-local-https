import json
from datetime import datetime
from pathlib import Path

import uvicorn
from logs import Logs
from index import buf_writer

logger = Logs.make_logger(Path(__file__).with_name("config.json"))

async def read_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body


async def app(scope, receive, send):
    assert scope["type"] == "http"
    assert scope["method"] == "POST"

    data = json.loads(await read_body(receive))
    data["datetime"] = datetime.fromisoformat(data["datetime"])
    _id = data["id"]
    data["id"] = str(_id)
    buf_writer.add_document(**data)
    logger.info(f"Record id^{_id} saved")

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


if __name__ == "__main__":
    try:
        ssl_certfile = Path(__file__).parent / "ssl/keycert.pem"
        uvicorn.run("buf_app:app", host="127.0.0.1", port=8000, ssl_certfile=ssl_certfile)
    except KeyboardInterrupt:
        buf_writer.close()
