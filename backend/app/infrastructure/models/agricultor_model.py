from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class AgricultorModel(Base):
    __tablename__ = 'agricultores'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, unique=True)
    telefono = Column(String(20), nullable=True)
    cedula = Column(String(20), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())