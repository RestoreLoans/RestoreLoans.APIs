from pydantic import BaseModel, EmailStr
from typing import Optional


class UpdateApplicationStatusRequest(BaseModel):
    email: EmailStr
    status: str
    notes: Optional[str] = None


class AssignRoleRequest(BaseModel):
    email: EmailStr          # the admin performing the change
    target_email: EmailStr   # the user whose role is being set
    role: str


class DeleteApplicationRequest(BaseModel):
    email: EmailStr
