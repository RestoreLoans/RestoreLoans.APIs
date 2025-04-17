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

class AlertCreate(BaseModel):
    title: str
    description: str
    is_active: bool

class AlertUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None

class AlertResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    is_active: bool
    status: AlertStatus
    date_time: datetime

    class Config:
        from_attributes= True
