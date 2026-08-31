from datetime import datetime, timedelta
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..models.user import User
from ..models.company import Company
from ..models.bank import BankDetail
from ..schemas.user import UserCreate, UserResponse, RegisterPayload
from ..schemas.company import CompanyCreate
from ..schemas.bank import BankDetailCreate
from ..utils.security import create_access_token, verify_password, get_password_hash
import random
import hashlib
import string
from app.schemas.user import UserResponse
from app.schemas.userRoles import UserRoleResponse
from app.services.email_service import email_service
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def some_method():
        pass  # Replace with actual implementation or remove if unnecessary

    def register_user(db: Session, payload: RegisterPayload):
        client = payload.clientDetails
        employer = payload.employerDetails
        bank = payload.bankDetails

        # Check if email already exists
        db_user = db.query(User).filter(User.email == client.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if ID number already exists
        db_user = db.query(User).filter(User.id_number == client.idNumber).first()
        if db_user:
            raise HTTPException(status_code=400, detail="ID number already registered")

        # Check if phone number already exists
        db_user = db.query(User).filter(User.phone_number == client.cellphoneNumber).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # Hash the password
        hashed_password = get_password_hash(client.password)

        # Parse dates
        dob = None
        if client.dob:
            if isinstance(client.dob, str):
                try:
                    # Accept yyyy-mm-dd or yyyy/mm/dd
                    dob_str = client.dob.replace('/', '-')
                    dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid DOB format")
            elif isinstance(client.dob, datetime):
                dob = client.dob.date()
            elif hasattr(client.dob, 'isoformat'):
                dob = client.dob
            else:
                raise HTTPException(status_code=400, detail="Invalid DOB format")

        # Create new user first
        db_user = User(
            first_name=client.name,
            last_name=client.surname,
            id_number=client.idNumber,
            email=client.email,
            phone_number=client.cellphoneNumber,
            gender=client.gender.lower(),  # assuming matches enum
            password=hashed_password,
            title=client.title,
            homephone=client.homephone,
            home_add1=client.homeAdd1,
            home_add2=client.homeAdd2,
            suburb=client.suburb,
            town=client.town,
            postal_code=client.code,
            language=client.language,
            dob=dob,
            nationality=client.nationality
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Create bank detail
        # Validate and map account_type to allowed enum values
        allowed_types = {"savings", "current", "cheque"}
        acct_type = bank.account_type.lower() if bank.account_type else None
        if acct_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid account_type: {acct_type}. Allowed: savings, current, cheque")

        db_bank = BankDetail(
            bank_name=bank.bank_name,
            branch_name=bank.branch_name,
            branch_code=bank.branch_code,
            account_holder_name=bank.account_holder_name,
            account_number=bank.account_number,
            account_type=acct_type,
            created_at=bank.created_at,
            updated_at=bank.updated_at
        )
        db.add(db_bank)
        db.commit()
        db.refresh(db_bank)

        # Create company
        pay_day_date = None
        if employer.payDayDate:
            try:
                pay_day_date = datetime.strptime(employer.payDayDate, "%Y/%m/%d").date()
            except ValueError:
                pass
        appointed_on_date = None
        if employer.appointedOnDate:
            try:
                appointed_on_date = datetime.strptime(employer.appointedOnDate, "%Y/%m/%d").date()
            except ValueError:
                pass
        contract_end_date = None
        if employer.contractEndDate:
            try:
                contract_end_date = datetime.strptime(employer.contractEndDate, "%Y/%m/%d").date()
            except ValueError:
                pass

        db_company = Company(
            name=employer.name,
            type=employer.type,
            pay_day_date=pay_day_date,
            address1=employer.address1,
            address2=employer.address2,
            town=employer.town,
            suburb=employer.suburb,
            post_code=employer.postCode,
            phone=employer.phone,
            appointed_on_date=appointed_on_date,
            pay_date_shift=employer.payDateShift,
            contact_method=employer.contactMethod,
            salary_freq=employer.salaryFeq,
            pay_method=employer.payMethod,
            pay_day_of_week=employer.payDayOfWeek,
            contract_end_date=contract_end_date,
            user_id=db_user.id
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)

        # Update user with company and bank ids
        db_user.company_id = db_company.id
        db_user.bank_id = db_bank.id
        db.commit()

        # Send new application notification to staff mailbox
        try:
            email_service.send_new_application_notification(
                applicant_name=f"{client.name} {client.surname}".strip(),
                applicant_phone=client.cellphoneNumber,
                applicant_email=client.email,
                id_number=client.idNumber,
                employer_name=(employer.name or ""),
            )
        except Exception as e:
            logging.error("Failed to send new application notification: %s", e)

        return db_user



    @staticmethod
    def login_user(db: Session, user_data: OAuth2PasswordRequestForm):
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not verify_password(user_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer","user": user}

    @staticmethod
    def forgot_password(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")

        # Generate OTP (in a real app, store this with expiry)
        otp = ''.join(random.choices(string.digits, k=6))
        return {"message": "OTP sent to registered phone", "otp": otp}  # Don't return OTP in production

    @staticmethod
    def forgot_username(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")
        return {"message": "Username sent to registered email"}

    @staticmethod
    def verify_otp(db: Session, phone_number: str, otp: str):
        # In real app, verify against stored OTP
        if len(otp) != 6 or not otp.isdigit():
            raise HTTPException(status_code=400, detail="Invalid OTP format")
        return {"message": "OTP verified successfully"}

    @staticmethod
    def user_roles(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        roles = db.query(UserRoleResponse).filter(UserRoleResponse.user_id == user_id).all()
        return {"user": UserResponse.from_orm(user), "roles": roles}
    
    @staticmethod
    def hash_password(password: str) -> str:
        # Hash the password using SHA-256
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    