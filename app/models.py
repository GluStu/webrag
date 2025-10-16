import uuid
from sqlalchemy import (
    Column, Text, Enum, DateTime, Integer, ForeignKey, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db import Base

INGESTION_STATUS = ("pending", "processing", "completed", "failed")

class Ingestion(Base):
    __tablename__ = "ingestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=False)
    status = Column(Enum(*INGESTION_STATUS, name="ingestion_status"), nullable=False, default="pending")
    title = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chunks = relationship("Chunk", back_populates="ingestion", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ingestions_status_created", "status", "created_at"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestions.id", ondelete="CASCADE"), index=True)
    url = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    vector_id = Column(Integer, nullable=False, unique=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ingestion = relationship("Ingestion", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("ingestion_id", "chunk_index", name="uq_ingestion_chunkindex"),
    )
