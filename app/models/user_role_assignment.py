from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base


# Roles recognised by the staff/admin dashboard.
#   admin   -> full control (view all, change any status, disburse, delete, manage roles)
#   manager -> view everything, review decisions (pending_approval / approved / rejected)
#   viewer  -> read only
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_VIEWER = "viewer"
VALID_ROLES = {ROLE_ADMIN, ROLE_MANAGER, ROLE_VIEWER}


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    role_name = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False)
