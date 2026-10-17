from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from apps.common.models import TimeStampedMixin
from core.db import Base


class User(TimeStampedMixin, Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150), default='')
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self):
        return f'<User {self.email}>'
