from pathlib import Path

from whoosh.analysis import NgramTokenizer
from whoosh.fields import DATETIME, ID, TEXT, SchemaClass
from whoosh.filedb.filestore import FileStorage
from whoosh.index import FileIndex
from whoosh.writing import BufferedWriter

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

buf_writer = BufferedWriter(ix, limit=10)
