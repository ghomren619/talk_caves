from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class User:
    sid: str
    username: str
    room_id: str


@dataclass
class Room:
    room_id: str
    users: Dict[str, User] = field(default_factory=dict)  # sid -> User
    admin_sid: Optional[str] = None


class RoomManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, Room] = {}
        self.sid_to_user: Dict[str, User] = {}

    def create_room(self) -> str:
        room_id = uuid.uuid4().hex[:8]
        self.rooms[room_id] = Room(room_id=room_id)
        return room_id

    def room_exists(self, room_id: str) -> bool:
        return room_id in self.rooms

    def get_room_user_count(self, room_id: str) -> int:
        room = self.rooms.get(room_id)
        return len(room.users) if room else 0

    def get_room_admin(self, room_id: str) -> Optional[str]:
        room = self.rooms.get(room_id)
        return room.admin_sid if room else None

    def is_room_admin(self, room_id: str, sid: str) -> bool:
        room = self.rooms.get(room_id)
        return bool(room and room.admin_sid == sid)

    def join_room(self, room_id: str, sid: str, username: str, as_admin: bool = False) -> None:
        room = self.rooms.get(room_id)
        if not room:
            raise ValueError("Room does not exist")

        user = User(sid=sid, username=username, room_id=room_id)
        room.users[sid] = user
        self.sid_to_user[sid] = user

        if as_admin or room.admin_sid is None:
            room.admin_sid = sid

    def leave_room(self, room_id: str, sid: str) -> None:
        room = self.rooms.get(room_id)
        if not room:
            return
        room.users.pop(sid, None)
        self.sid_to_user.pop(sid, None)

        if room.admin_sid == sid:
            # Promote any remaining user
            room.admin_sid = next(iter(room.users.keys()), None)

        if not room.users:
            # Clean up empty room
            self.rooms.pop(room_id, None)

    def get_user(self, sid: str) -> Optional[Dict[str, str]]:
        user = self.sid_to_user.get(sid)
        if not user:
            return None
        return {"sid": user.sid, "username": user.username, "room_id": user.room_id}


