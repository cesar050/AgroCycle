"""
Modelo ORM de Rol para SQLAlchemy.
SQLAlchemy necesita conocer todas las tablas que tienen relaciones
entre sí para poder resolver las foreign keys correctamente.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class RolModel(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
