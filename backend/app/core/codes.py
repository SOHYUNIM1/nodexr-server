from enum import Enum


class RoomCode(str, Enum):
    ROOM_CREATED = "ROOM200"
    ROOM_LIST_OK = "ROOM201"
    ROOM_USER_LIST_OK = "ROOM202"
    ROOM_INFO_OK = "ROOM203"
    ROOM_ENTER_OK = "ROOM204"

class UtteranceCode(str, Enum):
    UTT_SAVED = "UTT200"


ROOM_MESSAGE = {
    RoomCode.ROOM_CREATED: "회의실 생성 성공",
    RoomCode.ROOM_LIST_OK: "회의실 목록 조회 성공",
    RoomCode.ROOM_USER_LIST_OK: "회의실 참여자 목록 조회 성공",
    RoomCode.ROOM_INFO_OK: "회의실 정보 조회 성공",
    RoomCode.ROOM_ENTER_OK: "회의실 입장 성공",
}

UTTERANCE_MESSAGE = {
    UtteranceCode.UTT_SAVED : "발화 저장 성공"
}