"""
Modelo ORM de Usuario para SQLAlchemy.
Mapea la entidad de dominio Usuario a la tabla 'usuarios' de PostgreSQL.
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class UsuarioModel(Base):
    __tablename__ = 'usuarios'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    activo = Column(Boolean, default=True)
    correo_verificado = Column(Boolean, default=False)
    token_verificacion = Column(String(500), nullable=True)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
