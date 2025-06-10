from pydantic import BaseModel, Field # Use Field for Pydantic v2 examples if needed
from enum import Enum
from datetime import datetime
from typing import Optional # Import Optional

# --- Enums remain the same ---
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

# --- Corrected AlertCreate ---
class AlertCreate(BaseModel):
    # Required fields based on model (nullable=False, no server_default)
    user_id: int
    alert_type: AlertType
    message: str
    priority: PriorityLevel
    title: str
    description: str
    # Optional fields (nullable=True or has server_default)
    remarks: Optional[str] = None
    # You COULD include fields with server_default if you want to allow overriding them on creation:
    status: Optional[AlertStatus] = None
    action_required: Optional[bool] = None
    is_active: Optional[bool] = None
    is_read: Optional[bool] = None # Usually wouldn't set is_read on creation
    is_deleted: Optional[bool] = None # Usually wouldn't set is_deleted on creation

# --- Corrected AlertUpdate ---
class AlertUpdate(BaseModel):
    # Only include fields that make sense to update
    alert_type: Optional[AlertType] = None
    message: Optional[str] = None
    priority: Optional[PriorityLevel] = None
    status: Optional[AlertStatus] = None # e.g., setting to 'dismissed'
    action_required: Optional[bool] = None
    remarks: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_read: Optional[bool] = None # Can update read status
    is_deleted: Optional[bool] = None # Soft delete

# --- Corrected AlertResponse ---
class AlertResponse(BaseModel):
    # Include fields present in the database record
    id: int
    user_id: int
    alert_type: AlertType
    message: str
    date_time: datetime # Include the actual timestamp field from the model
    priority: PriorityLevel
    status: AlertStatus
    action_required: bool
    remarks: Optional[str] = None
    is_active: bool
    is_read: bool
    is_deleted: bool
    title: str
    description: str
    # Remove created_at/updated_at unless you add them to the model

    class Config:
        from_attributes = True # or orm_mode = True for Pydantic v1
