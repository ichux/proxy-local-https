import json
from datetime import datetime
from pathlib import Path

import uvicorn
from sqlite_utils import Database
from whoosh.index import LockError
from whoosh.writing import IndexingError

from index import buf_writer
from logs import Logs

logger = Logs.make_logger(Path(__file__).with_name("config.json"))
db = Database("failures.db")


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

    try:
        buf_writer.add_document(**data)
    except (IndexingError, LockError):
        reader = buf_writer._get_ram_reader()  # Represents the in-memory buffer
        # Save all data currently in buffer
        db["records"].insert_all([r for (_, r) in reader.iter_docs()])
        logger.info(f"Recovered from an error!")

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
        ssl_certfile = Path(__file__).parent / "ssl" / "keycert.pem"
        uvicorn.run(
            "buf_app:app", host="127.0.0.1", port=8000, ssl_certfile=ssl_certfile
        )
    except KeyboardInterrupt:
        buf_writer.close()
