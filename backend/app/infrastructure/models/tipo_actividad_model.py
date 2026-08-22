"""
Modelo ORM de TipoActividad para SQLAlchemy.
Catalogo de tipos de actividades agricolas.
Ya tiene datos iniciales cargados en la base de datos.
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class TipoActividadModel(Base):
    __tablename__ = 'tipos_actividad'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())