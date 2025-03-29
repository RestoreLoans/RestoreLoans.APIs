import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict

class OTPService:
    _otp_storage: Dict[str, dict] = {}  # In-memory storage for demo

    @staticmethod
    def generate_otp(phone_number: str) -> str:
        otp = ''.join(random.choices(string.digits, k=6))
        expiry = datetime.now() + timedelta(minutes=5)
        OTPService._otp_storage[phone_number] = {
            'otp': otp,
            'expiry': expiry
        }
        return otp

    @staticmethod
    def verify_otp(phone_number: str, otp: str) -> bool:
        stored = OTPService._otp_storage.get(phone_number)
        if not stored:
            return False
        if datetime.now() > stored['expiry']:
            return False
        return stored['otp'] == otp