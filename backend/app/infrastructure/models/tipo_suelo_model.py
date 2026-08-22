from sqlalchemy import Column, String, Boolean, Integer, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class TipoSueloModel(Base):
    __tablename__ = 'tipos_suelo'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    capacidad_retencion_agua = Column(Numeric(5, 2), nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())