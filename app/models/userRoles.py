from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, text
from app.database import Base  # Ensure Base is properly defined in app.database
import enum


class RoleStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class userRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, nullable=False)
    role_name = Column(String(200), nullable=False, unique=True)
    description = Column(String(200), nullable=True)
    status = Column(Enum(RoleStatus), nullable=False, server_default=RoleStatus.active.value)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))