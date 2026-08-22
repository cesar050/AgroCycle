from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class AgronomoModel(Base):
    __tablename__ = 'agronomos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey('usuarios.id'),
        nullable=False,
        unique=True
    )
    numero_registro = Column(String(50), nullable=False, unique=True)
    especialidad = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    firma_digital = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )