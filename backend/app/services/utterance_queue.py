import asyncio
from typing import Dict, Tuple

from app.schemas.utterances.utterances_req import UtterancesReq
from app.db.session import SessionLocal
from app.services.utterance_worker import process_utterance

_SESSION_QUEUES: Dict[str, asyncio.Queue] = {}
_SESSION_WORKERS: Dict[str, asyncio.Task] = {}

def _get_queue(session_id: str) -> asyncio.Queue:
    if session_id not in _SESSION_QUEUES:
        _SESSION_QUEUES[session_id] = asyncio.Queue()
    return _SESSION_QUEUES[session_id]

def _ensure_worker(session_id: str):
    if session_id not in _SESSION_WORKERS or _SESSION_WORKERS[session_id].done():
        _SESSION_WORKERS[session_id] = asyncio.create_task(_worker_loop(session_id))

async def enqueue_utterance(req: UtterancesReq) -> dict:
    sid = str(req.session_id)
    q = _get_queue(sid)
    _ensure_worker(sid)

    loop = asyncio.get_running_loop()
    fut = loop.create_future()

    await q.put((req, fut))
    return await fut

async def _worker_loop(session_id: str):
    q = _get_queue(session_id)

    while True:
        req, fut = await q.get()

        db = SessionLocal()
        try:
            graph_resp = await process_utterance(db, req)
            fut.set_result(graph_resp)
        except Exception as e:
            fut.set_exception(e)
        finally:
            db.close()
            q.task_done()