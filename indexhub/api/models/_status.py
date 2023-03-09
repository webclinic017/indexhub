import enum


class StatusTypes(str, enum.Enum):
    SUCCESS = "SUCCESS"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    UPDATE_FAILED = "UPDATE_FAILED"
