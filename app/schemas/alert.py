from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class AlertType(str, Enum):
    warning = "warning"
    error = "error"
    notification = "notification"
    success = "success"

class PriorityLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class AlertStatus(str, Enum):
    active = "active"
    dismissed = "dismissed"

class AlertBase(BaseModel):
    alert_type: AlertType
    message: str
    priority: PriorityLevel
    action_required: bool
    remarks: str = None

class AlertResponse(AlertBase):
    id: int
    user_id: int
    status: AlertStatus
    date_time: datetime

    class Config:
        orm_mode = True