from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class AlertType(str, enum.Enum):
    warning = "warning"
    error = "error"
    notification = "notification"
    success = "success"

class PriorityLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class AlertStatus(str, enum.Enum):
    active = "active"
    dismissed = "dismissed"

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, nullable=False) # Auto-incrementing PK
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    message = Column(String(200), nullable=False)
    date_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()')) # Has server default
    priority = Column(Enum(PriorityLevel), nullable=False)
    status = Column(Enum(AlertStatus), server_default="active", nullable=False)
    action_required = Column(Boolean,default=False, nullable=False)
    remarks = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_read = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=True, nullable=False)
    title = Column(String(200), nullable=False) # <-- Defined here
    description = Column(String(200), nullable=False) # <-- Also defined here