"""Identity anchor only; credentials, sessions and consent are not implemented here."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base, IdentityMixin


class User(IdentityMixin, Base):
    __tablename__ = "users"
    display_name: Mapped[str] = mapped_column(String(200))
