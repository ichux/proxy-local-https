import json
from datetime import datetime
from pathlib import Path

from logs import Logs
from sqlite_utils import Database
from whoosh.analysis import NgramTokenizer
from whoosh.fields import DATETIME, ID, TEXT, SchemaClass
from whoosh.filedb.filestore import FileStorage
from whoosh.index import FileIndex, LockError
from whoosh.writing import AsyncWriter, IndexingError

logger = Logs.make_logger(Path(__file__).with_name("config.json"))
db = Database("failures.db")

INDEX_NAME = "TAILLOG"
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
    _id = data["id"]
    data["id"] = str(_id)

    writer = AsyncWriter(ix)
    writer.add_document(**data)
    try:
        writer.commit()
    except (IndexingError, LockError):
        db["records"].insert(data)
        logger.info(f"Recovered from an error!")


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
