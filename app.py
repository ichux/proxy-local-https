import json
from datetime import datetime
from pathlib import Path

import aiohttp
from aiohttp.client_exceptions import ClientError, ClientOSError
from whoosh.analysis import NgramTokenizer
from whoosh.fields import DATETIME, ID, TEXT, SchemaClass
from whoosh.filedb.filestore import FileStorage
from whoosh.index import FileIndex
from whoosh.writing import AsyncWriter

from logs import Logs

logger = Logs.make_logger(Path(__file__).with_name("config.json"))

INDEX_NAME = "INDEX"
ix: FileIndex


class Schema(SchemaClass):
    id = ID(stored=True, unique=True, sortable=True)
    datetime = DATETIME(stored=True, sortable=True)
    emitter = TEXT(stored=True, sortable=True, analyzer=NgramTokenizer(4))
    log = TEXT(stored=True, sortable=True)

if not (INDEXED_DB := Path(__file__).parent / "index_db").exists():
    INDEXED_DB.mkdir(parents=True, exist_ok=True)
if (storage := FileStorage(INDEXED_DB)).index_exists(INDEX_NAME):
    ix = storage.open_index(INDEX_NAME)
else:
    ix = storage.create_index(Schema, INDEX_NAME)

async def wh_write(data):
    data["datetime"] = datetime.fromisoformat(data["datetime"])
    data["id"] = str(data["id"])
    writer = AsyncWriter(ix)
    writer.add_document(**data)
    writer.commit()



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
        except (ClientError, ClientOSError) as excecption:
            raise excecption

async def app(scope, receive, send):
    assert scope["type"] == "http"
    assert scope["method"] == "POST"

    body = json.loads(await read_body(receive))
    await wh_write(body)

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
