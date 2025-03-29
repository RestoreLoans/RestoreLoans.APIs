from typing import Optional
from fastapi import HTTPException
from ..models.user import User
from ..schemas.user import UserResponse

class EmailService:
    @staticmethod
    def send_welcome_email(email: str):
        # Implement email sending logic
        pass

    @staticmethod
    def send_password_reset_email(email: str, token: str):
        # Implement email sending logic
        pass