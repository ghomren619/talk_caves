from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socketio

from .rooms import RoomManager
from .schemas import CreateRoomResponse, RoomInfoResponse, JoinRoomPayload, MessagePayload, TypingPayload


# Socket.IO server configured for ASGI
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# FastAPI app for REST endpoints and middleware
app = FastAPI(title="Talk Caves Realtime Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_manager = RoomManager()


class CreateRoomRequest(BaseModel):
    username: str


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room() -> CreateRoomResponse:
    room_id = room_manager.create_room()
    return CreateRoomResponse(room_id=room_id)


@app.get("/rooms/{room_id}", response_model=RoomInfoResponse)
async def room_info(room_id: str) -> RoomInfoResponse:
    exists = room_manager.room_exists(room_id)
    users_count = room_manager.get_room_user_count(room_id) if exists else 0
    return RoomInfoResponse(exists=exists, users_count=users_count)


# Expose Socket.IO as the top-level ASGI app while preserving FastAPI
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


# Socket.IO event handlers
@sio.event
async def connect(sid: str, environ: Dict[str, Any]) -> None:
    # No-op on connect; join on explicit event
    pass


@sio.event
async def disconnect(sid: str) -> None:
    user = room_manager.get_user(sid)
    if not user:
        return
    room_id = user["room_id"]
    username = user["username"]
    was_admin = room_manager.is_room_admin(room_id, sid)

    room_manager.leave_room(room_id, sid)
    await sio.leave_room(sid, room_id)

    if room_manager.room_exists(room_id):
        await sio.emit(
            "user_left",
            {"username": username, "room_id": room_id, "users_count": room_manager.get_room_user_count(room_id)},
            room=room_id,
            skip_sid=sid,
        )

        # If admin left, promote another user
        if was_admin:
            new_admin_sid = room_manager.get_room_admin(room_id)
            if new_admin_sid:
                await sio.emit("admin_changed", {"room_id": room_id}, room=room_id)
    else:
        await sio.emit("room_closed", {"room_id": room_id})


@sio.event
async def create_room(sid: str, data: Dict[str, Any]) -> None:
    username = (data or {}).get("username")
    if not username:
        await sio.emit("error", {"message": "Username is required"}, to=sid)
        return

    room_id = room_manager.create_room()
    room_manager.join_room(room_id, sid, username, as_admin=True)
    await sio.enter_room(sid, room_id)

    await sio.emit("room_created", {"room_id": room_id, "admin": True}, to=sid)
    await sio.emit("user_joined", {"username": username, "room_id": room_id, "users_count": 1}, room=room_id)


@sio.event
async def join_room(sid: str, data: Dict[str, Any]) -> None:
    try:
        payload = JoinRoomPayload.model_validate(data or {})
    except Exception:
        await sio.emit("error", {"message": "Invalid join payload"}, to=sid)
        return

    if not room_manager.room_exists(payload.room_id):
        await sio.emit("error", {"message": "Room not found"}, to=sid)
        return

    room_manager.join_room(payload.room_id, sid, payload.username)
    await sio.enter_room(sid, payload.room_id)

    users_count = room_manager.get_room_user_count(payload.room_id)
    is_admin = room_manager.is_room_admin(payload.room_id, sid)

    await sio.emit(
        "joined_room",
        {"room_id": payload.room_id, "admin": is_admin, "users_count": users_count},
        to=sid,
    )
    await sio.emit(
        "user_joined",
        {"username": payload.username, "room_id": payload.room_id, "users_count": users_count},
        room=payload.room_id,
        skip_sid=sid,
    )


@sio.event
async def leave_room(sid: str, data: Dict[str, Any] | None = None) -> None:
    user = room_manager.get_user(sid)
    if not user:
        return
    room_id = user["room_id"]
    username = user["username"]
    was_admin = room_manager.is_room_admin(room_id, sid)

    room_manager.leave_room(room_id, sid)
    await sio.leave_room(sid, room_id)

    if room_manager.room_exists(room_id):
        await sio.emit(
            "user_left",
            {"username": username, "room_id": room_id, "users_count": room_manager.get_room_user_count(room_id)},
            room=room_id,
            skip_sid=sid,
        )
        if was_admin:
            new_admin_sid = room_manager.get_room_admin(room_id)
            if new_admin_sid:
                await sio.emit("admin_changed", {"room_id": room_id}, room=room_id)
    else:
        await sio.emit("room_closed", {"room_id": room_id})


@sio.event
async def message(sid: str, data: Dict[str, Any]) -> None:
    try:
        payload = MessagePayload.model_validate(data or {})
    except Exception:
        await sio.emit("error", {"message": "Invalid message payload"}, to=sid)
        return

    if not room_manager.room_exists(payload.room_id):
        await sio.emit("error", {"message": "Room not found"}, to=sid)
        return

    sender = room_manager.get_user(sid)
    if not sender:
        await sio.emit("error", {"message": "User not in a room"}, to=sid)
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    await sio.emit(
        "message",
        {
            "room_id": payload.room_id,
            "content": payload.content,
            "username": sender["username"],
            "timestamp": timestamp,
        },
        room=payload.room_id,
    )


@sio.event
async def typing(sid: str, data: Dict[str, Any]) -> None:
    try:
        payload = TypingPayload.model_validate(data or {})
    except Exception:
        await sio.emit("error", {"message": "Invalid typing payload"}, to=sid)
        return

    if not room_manager.room_exists(payload.room_id):
        return
    user = room_manager.get_user(sid)
    if not user:
        return
    await sio.emit(
        "typing",
        {"room_id": payload.room_id, "username": user["username"], "is_typing": payload.is_typing},
        room=payload.room_id,
        skip_sid=sid,
    )


