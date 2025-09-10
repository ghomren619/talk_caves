from __future__ import annotations

from pydantic import BaseModel, Field


class CreateRoomResponse(BaseModel):
    room_id: str = Field(...)


class RoomInfoResponse(BaseModel):
    exists: bool
    users_count: int


class JoinRoomPayload(BaseModel):
    room_id: str
    username: str


class MessagePayload(BaseModel):
    room_id: str
    content: str


class TypingPayload(BaseModel):
    room_id: str
    is_typing: bool


