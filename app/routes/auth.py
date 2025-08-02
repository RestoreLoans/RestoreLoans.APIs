from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserLogin, UserCreate, UserOTP, UserForgotPassword, UserForgotUsername, UserResponse
from app.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user_data)

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    return AuthService.login_user(db, user_data)

@router.post("/forgot-password")
def forgot_password(forgot_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.forgot_password(db, forgot_data.email)

@router.post("/forgot-username")
def forgot_username(forgot_data: UserForgotUsername, db: Session = Depends(get_db)):
    return AuthService.forgot_username(db, forgot_data.email)

@router.post("/verify-otp")
def verify_otp(otp_data: UserOTP, db: Session = Depends(get_db)):
    return AuthService.verify_otp(db, otp_data.phone_number, otp_data.otp)

@router.post("/resend-otp")
def resend_otp(otp_data: UserOTP, db: Session = Depends(get_db)):
    return AuthService.resend_otp(db, otp_data.phone_number)

@router.post("/send-otp")
def send_otp(otp_data: UserOTP, db: Session = Depends(get_db)):
    return AuthService.send_otp(db, otp_data.phone_number)

@router.post("/verify-username")
def verify_username(username_data: UserForgotUsername, db: Session = Depends(get_db)):
    return AuthService.verify_username(db, username_data.username, username_data.otp)

@router.post("/verify-password")
def verify_password(password_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.verify_password(db, password_data.email, password_data.otp)

@router.post("/reset-password")
def reset_password(password_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.reset_password(db, password_data.email, password_data.password)

@router.post("/reset-username") 
def reset_username(username_data: UserForgotUsername, db: Session = Depends(get_db)):
    return AuthService.reset_username(db, username_data.username, username_data.otp)

@router.post("/logout")     
def logout(db: Session = Depends(get_db)):
    return AuthService.logout_user(db)

@router.post("/change-password")        
def change_password(password_data: UserLogin, db: Session = Depends(get_db)):
    return AuthService.change_password(db, password_data.username, password_data.password)

@router.post("/update-profile")     
def update_profile(user_data: UserCreate, db: Session = Depends(get_db)):
    return AuthService.update_profile(db, user_data)

@router.post("/update-username")
def update_username(username_data: UserForgotUsername, db: Session = Depends(get_db)):
    return AuthService.update_username(db, username_data.username, username_data.otp)

@router.post("/update-password")
def update_password(password_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_password(db, password_data.email, password_data.password)

@router.post("/update-email")
def update_email(email_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_email(db, email_data.email, email_data.password)

@router.post("/update-phone")   
def update_phone(phone_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_phone(db, phone_data.phone_number, phone_data.password)

@router.post("/update-address")
def update_address(address_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_address(db, address_data.address, address_data.password)

@router.post("/update-profile-picture") 
def update_profile_picture(picture_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_profile_picture(db, picture_data.profile_picture, picture_data.password)

@router.post("/update-user-role")
def update_user_role(role_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_role(db, role_data.role, role_data.password)

@router.post("/update-user-status")
def update_user_status(status_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_status(db, status_data.status, status_data.password)

@router.post("/update-user-permissions")
def update_user_permissions(permissions_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_permissions(db, permissions_data.permissions, permissions_data.password)

@router.post("/update-user-preferences", operation_id="update_user_preferences_1")
def update_user_preferences(preferences_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_preferences(db, preferences_data.preferences, preferences_data.password)

@router.post("/update-user-notifications", operation_id="update_user_notifications_1")
def update_user_notifications(notifications_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_notifications(db, notifications_data.notifications, notifications_data.password)

@router.post("/update-user-settings", operation_id="update_user_settings_1")
def update_user_settings(settings_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_settings(db, settings_data.settings, settings_data.password)

@router.post("/update-user-privacy", operation_id="update_user_privacy_1")
def update_user_privacy(privacy_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_privacy(db, privacy_data.privacy, privacy_data.password)

@router.post("/update-user-security", operation_id="update_user_security_1")
def update_user_security(security_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_security(db, security_data.security, security_data.password)
     
@router.post("/update-user-activity")           
def update_user_activity(activity_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_activity(db, activity_data.activity, activity_data.password)

@router.post("/update-user-preferences", operation_id="update_user_preferences_default")
def update_user_preferences(preferences_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_preferences(db, preferences_data.preferences, preferences_data.password)

@router.post("/update-user-notifications")  
def update_user_notifications(notifications_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_notifications(db, notifications_data.notifications, notifications_data.password)

@router.post("/update-user-settings", operation_id="update_user_settings_unique")
def update_user_settings(settings_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_settings(db, settings_data.settings, settings_data.password)

@router.post("/update-user-privacy")        
def update_user_privacy(privacy_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_privacy(db, privacy_data.privacy, privacy_data.password)

@router.post("/update-user-security")   
def update_user_security(security_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_security(db, security_data.security, security_data.password)

@router.post("/update-user-activity", operation_id="update_user_activity_1")
def update_user_activity(activity_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_activity(db, activity_data.activity, activity_data.password)

@router.post("/update_user_preferences", operation_id="update_user_preferences_unique")
def update_user_preferences(preferences_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_preferences(db, preferences_data.preferences, preferences_data.password)

@router.post("/update-user-notifications", operation_id="update_user_notifications_unique")
def update_user_notifications(notifications_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_notifications(db, notifications_data.notifications, notifications_data.password)

@router.post("/update-user-settings")
def update_user_settings(settings_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_settings(db, settings_data.settings, settings_data.password)

@router.post("/update-user-privacy", operation_id="update_user_privacy_unique")
def update_user_privacy(privacy_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_privacy(db, privacy_data.privacy, privacy_data.password)

@router.post("/update-user-security", operation_id="update_user_security_unique")
def update_user_security(security_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_security(db, security_data.security, security_data.password)

@router.post("/update-user-activity", operation_id="update_user_activity_unique")
def update_user_activity(activity_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_activity(db, activity_data.activity, activity_data.password)

@router.post("/update-user-preferences")
def update_user_preferences(preferences_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.update_user_preferences(db, preferences_data.preferences, preferences_data.password)