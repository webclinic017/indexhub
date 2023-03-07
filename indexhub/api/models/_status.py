import enum


class StatusTypes(str, enum.ENUM):
    SUCCESS = "SUCCESS"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    UPDATE_FAILED = "UPDATE_FAILED"
