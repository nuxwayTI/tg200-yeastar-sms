
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import os
import time
import requests

app = FastAPI(title="TG200 Yeastar SMS Provider")

API_KEY = os.getenv("API_KEY", "change-me")
YEASTAR_WEBHOOK_URL = os.getenv("YEASTAR_WEBHOOK_URL", "")

sms_queue = []
results = {}
connected_agents = {}


class SmsRequest(BaseModel):
    from_number: Optional[str] = Field(default=None, alias="from")
    to: str
    text: Optional[str] = ""
    media_urls: Optional[List[str]] = []


def check_auth(authorization: Optional[str]):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail={
            "errors": [{
                "code": "10004",
                "title": "Authentication failed",
                "detail": "Invalid API key"
            }]
        })


@app.get("/")
def home():
    return {
        "service": "TG200 Yeastar SMS Provider",
        "status": "running"
    }


@app.get("/verify", response_class=PlainTextResponse)
def verify(challenge: str, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    return challenge


@app.post("/sendmessage")
async def sendmessage(payload: SmsRequest, authorization: Optional[str] = Header(None)):
    check_auth(authorization)

    message_id = str(uuid.uuid4())

    sms_queue.append({
        "id": message_id,
        "from": payload.from_number,
        "to": payload.to,
        "text": payload.text or "",
        "media_urls": payload.media_urls or [],
        "created_at": time.time(),
        "status": "queued"
    })

    return {"data": {"id": message_id}}


@app.get("/agent/poll")
def agent_poll(agent_id: str, agent_key: str):
    if agent_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid agent key")

    connected_agents[agent_id] = time.time()

    if not sms_queue:
        return {"job": None}

    job = sms_queue.pop(0)
    return {"job": job}


@app.post("/agent/result")
async def agent_result(request: Request, agent_key: str):
    if agent_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid agent key")

    data = await request.json()
    message_id = data.get("id")

    if message_id:
        results[message_id] = data

    return {"ok": True}


@app.post("/agent/inbound")
async def agent_inbound(request: Request, agent_key: str):
    if agent_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid agent key")

    inbound = await request.json()

    if not YEASTAR_WEBHOOK_URL:
        return {"ok": False, "detail": "YEASTAR_WEBHOOK_URL not configured"}

    payload = {
        "data": {
            "event_type": "message.received",
            "id": str(uuid.uuid4()),
            "occurred_at": inbound.get("received_at"),
            "payload": {
                "id": inbound.get("id", str(uuid.uuid4())),
                "from": {
                    "phone_number": inbound.get("sender")
                },
                "to": [
                    {
                        "phone_number": inbound.get("to", "")
                    }
                ],
                "text": inbound.get("content", ""),
                "received_at": inbound.get("received_at"),
                "record_type": "message",
                "direction": "inbound",
                "type": "SMS"
            },
            "record_type": "event"
        }
    }

    response = requests.post(YEASTAR_WEBHOOK_URL, json=payload, timeout=20)

    return {
        "ok": response.status_code in [200, 204],
        "status_code": response.status_code
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "queued": len(sms_queue),
        "agents": connected_agents,
        "results": results
    }
