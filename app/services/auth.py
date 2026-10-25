from datetime import datetime, timedelta, timezone
from typing import Optional
import enum

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..models.user import User
from ..models.company import Company
from ..models.bank import BankDetail
from ..models.password_reset import PasswordResetToken
from ..models.profile_picture import UserProfilePicture
from ..models.loan import Loan
from ..models.document import Document
from ..models.loan_application import LoanApplication, IN_PROGRESS_STATUSES
from .roles import RoleService
from ..schemas.user import UserCreate, UserResponse, RegisterPayload, ProfileUpdatePayload
from ..schemas.company import CompanyCreate
from ..schemas.bank import BankDetailCreate
from ..utils.security import create_access_token, verify_password, get_password_hash
import os
import random
import hashlib
import secrets
import string
from app.schemas.user import UserResponse
from app.schemas.userRoles import UserRoleResponse
from app.services.email_service import email_service
import logging

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password reset code settings
RESET_OTP_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_OTP_TTL_MINUTES", "15"))
RESET_OTP_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_OTP_MAX_ATTEMPTS", "5"))
RESET_OTP_RESEND_COOLDOWN_SECONDS = int(
    os.getenv("PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS", "60")
)
MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))

# Customers may only refresh their documents/profile details after this many
# days from their last document upload or loan application.
DOCUMENT_REFRESH_DAYS = int(os.getenv("DOCUMENT_REFRESH_DAYS", "90"))


def _utcnow() -> datetime:
    # Naive UTC, matching the naive DateTime columns used across the models.
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
            employment_status=(getattr(employer, "employmentStatus", None) or None),
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
        except Exception:
            logging.exception("Failed to send new application notification")

        # Send welcome acknowledgement email to the newly registered user
        try:
            email_service.send_welcome_email(
                first_name=client.name,
                last_name=client.surname,
                to_email=client.email,
            )
        except Exception:
            logging.exception("Failed to send welcome email")

        return db_user



    @staticmethod
    def login_user(db: Session, user_data: OAuth2PasswordRequestForm):
        user = db.query(User).filter(User.email == user_data.email).first()
        now = _utcnow()

        # Account locked after 3 failed attempts
        if user and getattr(user, "locked_until", None) and user.locked_until > now:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to 3 failed login attempts. Try again later.",
            )

        if not user or not verify_password(user_data.password, user.password):
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 3:
                    user.locked_until = now + timedelta(minutes=15)
                db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Success: reset counters and record last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        db.commit()

        access_token = create_access_token(data={"sub": user.email})
        role = RoleService.get_user_role(db, user)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
            "role": role,
        }

    @staticmethod
    def get_profile(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        dob = user.dob.isoformat() if user.dob else None

        picture = (
            db.query(UserProfilePicture)
            .filter(UserProfilePicture.user_id == user.id)
            .first()
        )

        client_details = {
            "profilePicture": picture.picture if picture else None,
            "idNumber": user.id_number,
            "cellphoneNumber": user.phone_number,
            "homephone": user.homephone,
            "homeAdd1": user.home_add1,
            "homeAdd2": user.home_add2,
            "suburb": user.suburb,
            "town": user.town,
            "code": user.postal_code,
            "title": user.title,
            "name": user.first_name,
            "surname": user.last_name,
            "email": user.email,
            "password": "",
            "language": user.language,
            "dob": dob,
            "nationality": user.nationality,
            "gender": user.gender.value if isinstance(user.gender, enum.Enum) else user.gender,
        }

        employer_details = None
        if user.company:
            company = user.company
            employer_details = {
                "name": company.name,
                "type": company.type,
                "payDayDate": company.pay_day_date.isoformat() if company.pay_day_date else None,
                "address1": company.address1,
                "address2": company.address2,
                "town": company.town,
                "suburb": company.suburb,
                "postCode": company.post_code,
                "phone": company.phone,
                "appointedOnDate": company.appointed_on_date.isoformat() if company.appointed_on_date else None,
                "payDateShift": company.pay_date_shift,
                "contactMethod": company.contact_method,
                "salaryFeq": company.salary_freq,
                "payMethod": company.pay_method,
                "payDayOfWeek": company.pay_day_of_week,
                "contractEndDate": company.contract_end_date.isoformat() if company.contract_end_date else None,
                "employmentStatus": company.employment_status,
            }

        bank_details = None
        if user.bank:
            bank = user.bank
            bank_details = {
                "bank_name": bank.bank_name,
                "custom_bank_name": None,
                "branch_name": bank.branch_name,
                "branch_code": bank.branch_code,
                "account_holder_name": bank.account_holder_name,
                "account_number": bank.account_number,
                "account_type": bank.account_type.value if isinstance(bank.account_type, enum.Enum) else bank.account_type,
                "created_at": bank.created_at.date().isoformat() if bank.created_at else None,
                "updated_at": bank.updated_at.date().isoformat() if bank.updated_at else None,
            }

        return {
            "clientDetails": client_details,
            "employerDetails": employer_details,
            "bankDetails": bank_details,
        }

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        if hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day"):
            return value
        try:
            return datetime.strptime(str(value).replace("/", "-"), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def _in_progress_application(db: Session, user_id: int):
        return (
            db.query(LoanApplication)
            .join(Loan, Loan.id == LoanApplication.loan_id)
            .filter(
                Loan.user_id == user_id,
                LoanApplication.status.in_(IN_PROGRESS_STATUSES),
            )
            .first()
        )

    @staticmethod
    def update_eligibility(db: Session, email: str):
        """Report whether a customer may edit their profile / refresh documents."""
        user = (
            db.query(User)
            .filter(User.email == (email or "").strip().lower())
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        in_progress = AuthService._in_progress_application(db, user.id)

        # Newest document upload, falling back to the most recent loan
        # application date (documents are attached to applications).
        last_doc_date = None
        latest_doc = (
            db.query(Document)
            .filter(Document.user_id == user.id)
            .order_by(Document.upload_date.desc())
            .first()
        )
        if latest_doc and latest_doc.upload_date:
            last_doc_date = (
                latest_doc.upload_date.date()
                if isinstance(latest_doc.upload_date, datetime)
                else latest_doc.upload_date
            )
        latest_loan = (
            db.query(Loan)
            .filter(Loan.user_id == user.id)
            .order_by(Loan.created_at.desc())
            .first()
        )
        if latest_loan and latest_loan.created_at:
            loan_date = (
                latest_loan.created_at.date()
                if isinstance(latest_loan.created_at, datetime)
                else latest_loan.created_at
            )
            if last_doc_date is None or loan_date > last_doc_date:
                last_doc_date = loan_date

        next_update_date = None
        can_update_documents = True
        if last_doc_date:
            next_update_date = last_doc_date + timedelta(days=DOCUMENT_REFRESH_DAYS)
            can_update_documents = (
                datetime.now(timezone.utc).date() >= next_update_date
            )

        return {
            "canUpdateProfile": not bool(in_progress),
            "canUpdateDocuments": can_update_documents,
            "inProgress": bool(in_progress),
            "reason": (
                "You cannot change your profile while a loan application is "
                "still in progress."
                if in_progress
                else None
            ),
            "lastDocumentDate": last_doc_date.isoformat() if last_doc_date else None,
            "nextUpdateDate": next_update_date.isoformat() if next_update_date else None,
        }

    @staticmethod
    def update_profile_full(db: Session, payload: ProfileUpdatePayload):
        """Update the customer's client, employer and bank details.

        Refuses the change while a loan application is still in progress.
        """
        client = payload.clientDetails
        employer = payload.employerDetails
        bank = payload.bankDetails

        user = db.query(User).filter(User.email == client.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if AuthService._in_progress_application(db, user.id):
            raise HTTPException(
                status_code=409,
                detail=(
                    "You cannot change your profile while a loan application "
                    "is still in progress."
                ),
            )

        user.first_name = client.name or user.first_name
        user.last_name = client.surname or user.last_name
        user.id_number = client.idNumber or user.id_number
        user.phone_number = client.cellphoneNumber or user.phone_number
        if client.gender:
            user.gender = client.gender.lower()
        user.title = client.title
        user.homephone = client.homephone
        user.home_add1 = client.homeAdd1
        user.home_add2 = client.homeAdd2
        user.suburb = client.suburb
        user.town = client.town
        user.postal_code = client.code
        user.language = client.language
        user.nationality = client.nationality
        # Only overwrite the date of birth when one was submitted, so a blank
        # field on the edit form cannot silently wipe the stored value.
        if client.dob is not None:
            user.dob = AuthService._parse_date(client.dob)

        company = db.query(Company).filter(Company.user_id == user.id).first()
        if company is None:
            company = Company(user_id=user.id)
            db.add(company)
        company.name = employer.name
        company.type = employer.type
        company.pay_day_date = AuthService._parse_date(employer.payDayDate)
        company.address1 = employer.address1
        company.address2 = employer.address2
        company.town = employer.town
        company.suburb = employer.suburb
        company.post_code = employer.postCode
        company.phone = employer.phone
        company.appointed_on_date = AuthService._parse_date(employer.appointedOnDate)
        company.pay_date_shift = employer.payDateShift
        company.contact_method = employer.contactMethod
        company.salary_freq = employer.salaryFeq
        company.pay_method = employer.payMethod
        company.pay_day_of_week = employer.payDayOfWeek
        company.contract_end_date = AuthService._parse_date(employer.contractEndDate)
        if getattr(employer, "employmentStatus", None):
            company.employment_status = employer.employmentStatus
        db.flush()
        user.company_id = company.id

        allowed_types = {"savings", "current", "cheque"}
        acct_type = (bank.account_type or "").lower()
        bank_row = None
        if user.bank_id:
            bank_row = (
                db.query(BankDetail).filter(BankDetail.id == user.bank_id).first()
            )
        if bank_row is None:
            bank_row = BankDetail(account_type=acct_type if acct_type in allowed_types else "cheque")
            db.add(bank_row)
        elif acct_type in allowed_types:
            bank_row.account_type = acct_type
        bank_row.bank_name = bank.bank_name or bank_row.bank_name or "Unknown"
        bank_row.branch_name = bank.branch_name
        bank_row.branch_code = bank.branch_code
        bank_row.account_holder_name = bank.account_holder_name
        bank_row.account_number = bank.account_number or bank_row.account_number or "0"
        db.flush()
        user.bank_id = bank_row.id

        db.commit()
        db.refresh(user)
        return AuthService.get_profile(db, user.email)

    @staticmethod
    def _hash_reset_otp(email: str, otp: str) -> str:
        return hashlib.sha256(
            f"{email.strip().lower()}:{otp}".encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _active_reset_token(
        db: Session, email: str
    ) -> Optional[PasswordResetToken]:
        return (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.email == email,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > _utcnow(),
            )
            .order_by(PasswordResetToken.id.desc())
            .first()
        )

    @staticmethod
    def forgot_password(db: Session, email: str):
        """Email a single-use 6-digit reset code to a registered user."""
        email = email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")

        now = _utcnow()

        # Throttle repeat requests so the mailbox cannot be spammed.
        pending = AuthService._active_reset_token(db, email)
        if pending and pending.created_at:
            elapsed = (now - pending.created_at).total_seconds()
            wait = int(RESET_OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            if wait > 0:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "A reset code was just sent. Please wait "
                        f"{wait} second(s) before requesting another one."
                    ),
                )

        # Any earlier code becomes unusable once a new one is issued.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.used_at.is_(None),
        ).update({"used_at": now}, synchronize_session=False)

        otp = "".join(secrets.choice(string.digits) for _ in range(6))
        token = PasswordResetToken(
            user_id=user.id,
            email=email,
            otp_hash=AuthService._hash_reset_otp(email, otp),
            attempts=0,
            expires_at=now + timedelta(minutes=RESET_OTP_TTL_MINUTES),
            created_at=now,
        )
        db.add(token)
        db.commit()
        db.refresh(token)

        try:
            email_service.send_password_reset_email(
                to_email=email,
                first_name=user.first_name,
                otp=otp,
                expires_minutes=RESET_OTP_TTL_MINUTES,
            )
        except Exception as e:
            # Do not leave a code the user never received blocking retries.
            token.used_at = _utcnow()
            db.commit()
            logging.error("Failed to send password reset email: %s", e)
            raise HTTPException(
                status_code=502,
                detail=(
                    "We could not send the reset email right now. Please try "
                    "again in a moment, or contact support."
                ),
            )

        return {
            "message": (
                f"A 6-digit reset code was sent to {email}. It expires in "
                f"{RESET_OTP_TTL_MINUTES} minutes."
            ),
            "expires_in_minutes": RESET_OTP_TTL_MINUTES,
        }

    @staticmethod
    def verify_reset_otp(db: Session, email: str, otp: str):
        """Check a reset code without consuming it (used before the new password step)."""
        email = email.strip().lower()
        token = AuthService._active_reset_token(db, email)
        if not token:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This reset code has expired or is no longer valid. "
                    "Please request a new one."
                ),
            )

        if not otp or not otp.isdigit() or len(otp) != 6:
            raise HTTPException(
                status_code=400, detail="The reset code must be 6 digits."
            )

        if token.attempts >= RESET_OTP_MAX_ATTEMPTS:
            token.used_at = _utcnow()
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=(
                    "Too many incorrect attempts. Please request a new reset "
                    "code."
                ),
            )

        if token.otp_hash != AuthService._hash_reset_otp(email, otp):
            token.attempts = (token.attempts or 0) + 1
            db.commit()
            remaining = max(RESET_OTP_MAX_ATTEMPTS - token.attempts, 0)
            raise HTTPException(
                status_code=400,
                detail=(
                    "Incorrect reset code. "
                    f"{remaining} attempt(s) remaining."
                ),
            )

        return {"message": "Reset code verified.", "verified": True}

    @staticmethod
    def reset_password(
        db: Session,
        email: str,
        otp: str,
        new_password: str,
        confirm_password: Optional[str] = None,
    ):
        """Consume a valid reset code and store the new password hash."""
        email = email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")

        if confirm_password is not None and new_password != confirm_password:
            raise HTTPException(
                status_code=400, detail="The passwords do not match."
            )
        if len(new_password or "") < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
                ),
            )

        token = AuthService._active_reset_token(db, email)
        if not token:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This reset code has expired or is no longer valid. "
                    "Please request a new one."
                ),
            )

        if token.attempts >= RESET_OTP_MAX_ATTEMPTS:
            token.used_at = _utcnow()
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=(
                    "Too many incorrect attempts. Please request a new reset "
                    "code."
                ),
            )

        if token.otp_hash != AuthService._hash_reset_otp(email, otp or ""):
            token.attempts = (token.attempts or 0) + 1
            db.commit()
            remaining = max(RESET_OTP_MAX_ATTEMPTS - token.attempts, 0)
            raise HTTPException(
                status_code=400,
                detail=(
                    "Incorrect reset code. "
                    f"{remaining} attempt(s) remaining."
                ),
            )

        user.password = get_password_hash(new_password)
        token.used_at = _utcnow()

        # Invalidate any other outstanding codes for this address.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.email == email,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.id != token.id,
        ).update({"used_at": token.used_at}, synchronize_session=False)

        db.commit()

        try:
            email_service.send_password_changed_email(
                to_email=email, first_name=user.first_name
            )
        except Exception as e:
            logging.error("Failed to send password changed email: %s", e)

        return {
            "message": (
                "Password updated successfully. You can now log in with your "
                "new password."
            )
        }

    @staticmethod
    def update_profile_picture(db: Session, email: str, picture: str):
        """Create or replace the stored avatar for the given user."""
        email = (email or "").strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        picture = (picture or "").strip()
        if not picture:
            raise HTTPException(
                status_code=400, detail="A profile picture is required."
            )
        if not picture.startswith("data:image/"):
            raise HTTPException(
                status_code=400,
                detail="Profile picture must be a valid image data URL.",
            )
        # Guard against very large uploads bloating the row (~5 MB of base64).
        if len(picture) > 5_000_000:
            raise HTTPException(
                status_code=400, detail="Profile picture is too large."
            )

        now = _utcnow()
        record = (
            db.query(UserProfilePicture)
            .filter(UserProfilePicture.user_id == user.id)
            .first()
        )
        if record:
            record.picture = picture
            record.updated_at = now
        else:
            record = UserProfilePicture(
                user_id=user.id, picture=picture, updated_at=now
            )
            db.add(record)

        db.commit()
        db.refresh(record)

        return {
            "message": "Profile picture updated successfully.",
            "profile_picture": record.picture,
        }

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
    