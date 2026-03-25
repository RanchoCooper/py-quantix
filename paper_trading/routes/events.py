"""
SSE 事件流路由
"""
import asyncio
import json
from datetime import date

from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

router = APIRouter(prefix="/api/events", tags=["事件"])


async def sse_stream(request: Request):
    """SSE 事件流"""
    app = request.app
    running = getattr(app.state, "running", False)
    event_queue = getattr(app.state, "event_queue", None)
    if not running or event_queue is None:
        return

    while getattr(app.state, "running", False):
        try:
            event = await asyncio.wait_for(
                getattr(app.state, "event_queue", None).get(),
                timeout=30.0,
            )
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], default=str),
            }
        except asyncio.TimeoutError:
            yield {"event": "heartbeat", "data": json.dumps({"time": str(date.today())})}
        except Exception:
            break


@router.get("/stream")
async def events_stream(request: Request):
    """SSE 实时推送端点"""
    return EventSourceResponse(sse_stream(request))
