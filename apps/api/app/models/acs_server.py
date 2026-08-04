from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class AcsServer(Base):
    __tablename__ = "acs_servers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    bearer_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    verify_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    online_threshold_s: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
