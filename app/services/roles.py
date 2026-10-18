"""Staff role resolution for the admin/manager/viewer dashboard.

Roles are stored in the `user_role_assignments` table (one role per user). The
first administrators can be bootstrapped from environment variables so the
system is usable before any role exists in the database:

    ADMIN_EMAILS=admin@restoreloans.co.za,owner@restoreloans.co.za
    MANAGER_EMAILS=manager@restoreloans.co.za
    VIEWER_EMAILS=viewer@restoreloans.co.za
"""
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_role_assignment import (
    UserRoleAssignment,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_VIEWER,
    VALID_ROLES,
)
import os

# Statuses each role is allowed to set on a loan application.
MANAGER_ALLOWED_STATUSES = {"pending_approval", "approved", "rejected"}
ADMIN_ALLOWED_STATUSES = {
    "pending_approval",
    "approved",
    "rejected",
    "disbursed",
    "completed",
    "defaulted",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Fallback bootstrap administrator(s) used only when ADMIN_EMAILS is not set in
# the environment, so the system is usable out of the box.
DEFAULT_ADMIN_EMAILS = "docsrestoreloan@gmail.com"


def _env_emails(name: str) -> set:
    raw = os.getenv(name, "") or ""
    if not raw and name == "ADMIN_EMAILS":
        raw = DEFAULT_ADMIN_EMAILS
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _bootstrap_role_for_email(email: str) -> Optional[str]:
    email = (email or "").strip().lower()
    if not email:
        return None
    if email in _env_emails("ADMIN_EMAILS"):
        return ROLE_ADMIN
    if email in _env_emails("MANAGER_EMAILS"):
        return ROLE_MANAGER
    if email in _env_emails("VIEWER_EMAILS"):
        return ROLE_VIEWER
    return None


class RoleService:
    @staticmethod
    def is_supported_role(role: str) -> bool:
        return (role or "").strip().lower() in VALID_ROLES

    @staticmethod
    def get_user_role(db: Session, user: User) -> Optional[str]:
        """Return the stored role for a user, bootstrapping from env if needed."""
        if not user:
            return None

        assignment = (
            db.query(UserRoleAssignment)
            .filter(UserRoleAssignment.user_id == user.id)
            .first()
        )
        if assignment:
            return assignment.role_name

        boot_role = _bootstrap_role_for_email(user.email)
        if boot_role:
            db.add(
                UserRoleAssignment(
                    user_id=user.id, role_name=boot_role, created_at=_utcnow()
                )
            )
            db.commit()
            return boot_role
        return None

    @staticmethod
    def get_role_by_email(db: Session, email: str) -> Optional[str]:
        if not email:
            return None
        user = db.query(User).filter(User.email == (email or "").strip().lower()).first()
        if not user:
            return None
        return RoleService.get_user_role(db, user)

    @staticmethod
    def require_role(db: Session, email: str, allowed: set) -> str:
        """Raise 401/403 unless the caller's role is one of `allowed`."""
        role = RoleService.get_role_by_email(db, email)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You do not have staff access.",
            )
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return role

    @staticmethod
    def can_set_status(role: str, new_status: str) -> bool:
        new_status = (new_status or "").strip().lower()
        if role == ROLE_ADMIN:
            return new_status in ADMIN_ALLOWED_STATUSES
        if role == ROLE_MANAGER:
            return new_status in MANAGER_ALLOWED_STATUSES
        return False

    @staticmethod
    def set_role(db: Session, user: User, role: str) -> str:
        role = (role or "").strip().lower()
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: {', '.join(sorted(VALID_ROLES))}",
            )

        assignment = (
            db.query(UserRoleAssignment)
            .filter(UserRoleAssignment.user_id == user.id)
            .first()
        )
        if assignment:
            assignment.role_name = role
        else:
            db.add(
                UserRoleAssignment(
                    user_id=user.id, role_name=role, created_at=_utcnow()
                )
            )
        db.commit()
        return role

    @staticmethod
    def list_staff(db: Session) -> List[dict]:
        rows = (
            db.query(UserRoleAssignment, User)
            .join(User, User.id == UserRoleAssignment.user_id)
            .order_by(UserRoleAssignment.role_name, User.email)
            .all()
        )
        return [
            {
                "userId": user.id,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "role": assignment.role_name,
                "createdAt": assignment.created_at.isoformat()
                if assignment.created_at
                else None,
            }
            for assignment, user in rows
        ]
