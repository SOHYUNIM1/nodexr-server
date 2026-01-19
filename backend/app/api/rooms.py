import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.room import Room
from app.db.models.user import User
from app.schemas.room import (
    RoomCreate,
    RoomListDTO,
    RoomInfoDTO
)
from app.schemas.user import UserCreate, UserDTO
from app.schemas.response import ApiResponse
from app.core.codes import RoomCode, ROOM_MESSAGE

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])

@router.post("/generate", response_model=ApiResponse)
def generate_room(req: RoomCreate, db: Session = Depends(get_db)):
    room = Room(
        room_topic=req.room_topic,
        password=req.password
    )
    db.add(room)
    db.flush()

    user = User(
        room_id=room.room_id,
        nickname=req.nickname,
        leader=True
    )
    db.add(user)
    db.commit()

    return ApiResponse(
        code=RoomCode.ROOM_CREATED,
        message=ROOM_MESSAGE[RoomCode.ROOM_CREATED],
        result={
            "room_id": room.room_id,
            "room_topic": room.room_topic,
            "password": room.password,
            "leader": req.nickname
        }
    )

@router.get("/list", response_model=ApiResponse)
def list_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).all()

    return ApiResponse(
        code=RoomCode.ROOM_LIST_OK,
        message=ROOM_MESSAGE[RoomCode.ROOM_LIST_OK],
        result={
            "rooms": [
                RoomListDTO(
                    room_id=r.room_id,
                    room_topic=r.room_topic
                ) for r in rooms
            ]
        }
    )

@router.get("/users", response_model=ApiResponse)
def room_users(room_id: uuid.UUID, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.room_id == room_id).all()

    return ApiResponse(
        code=RoomCode.ROOM_USER_LIST_OK,
        message=ROOM_MESSAGE[RoomCode.ROOM_USER_LIST_OK],
        result={
            "users": [
                UserDTO(
                    nickname=u.nickname,
                    leader=u.leader
                ) for u in users
            ]
        }
    )

@router.get("/info", response_model=ApiResponse)
def room_info(room_id: uuid.UUID, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.room_id == room_id).first()
    users = db.query(User).filter(User.room_id == room_id).all()

    return ApiResponse(
        code=RoomCode.ROOM_INFO_OK,
        message=ROOM_MESSAGE[RoomCode.ROOM_INFO_OK],
        result=RoomInfoDTO(
            room_topic=room.room_topic,
            users=[
                UserDTO(
                    nickname=u.nickname,
                    leader=u.leader
                ) for u in users
            ]
        )
    )

@router.post("/enter", response_model=ApiResponse)
def enter_room(req: UserCreate, db: Session = Depends(get_db)):
    user = User(
        room_id=req.room_id,
        nickname=req.nickname,
        leader=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(
        code=RoomCode.ROOM_ENTER_OK,
        message=ROOM_MESSAGE[RoomCode.ROOM_ENTER_OK],
        result={
            "user_id": user.user_id
        }
    )