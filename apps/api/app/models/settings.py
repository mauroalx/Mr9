from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.core.database import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    installed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Sao_Paulo")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="pt-BR")
    approved_dns: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    online_threshold_s: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    diagnostic_cooldown_s: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    diagnostic_timeout_s: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
