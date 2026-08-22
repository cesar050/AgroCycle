from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class CultivoModel(Base):
    __tablename__ = 'cultivos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    nombre_cientifico = Column(String(150), nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())