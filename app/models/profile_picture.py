from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from app.database import Base


class UserProfilePicture(Base):
    __tablename__ = "user_profile_pictures"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Stored as a base64 data URL (e.g. "data:image/jpeg;base64,....").
    picture = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False)
