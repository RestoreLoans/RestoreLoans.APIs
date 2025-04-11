from pydantic import BaseModel, field_validator
from enum import Enum
from datetime import date, datetime
from typing import Optional

class RoleStatus(str, Enum):
    active = "active"
    inactive = "inactive"

class userRoleBase(BaseModel):
    role_name: str
    description: Optional[str] = None
    status: RoleStatus

class UserRoleCreate(userRoleBase):
    pass

class UserRoleResponse(userRoleBase):
    id: int
    created_at: date

    @field_validator("created_at", mode="before")
    def parse_datetime_to_date(cls, value):
        if isinstance(value, datetime):
            return value.date()
        return value

    class Config:
        from_attributes = True