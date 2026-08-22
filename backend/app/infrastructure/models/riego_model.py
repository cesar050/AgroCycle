"""
Modelo ORM de Riego para SQLAlchemy.
Detalle especifico de una actividad de riego.
El aporte hidrico estimado se calcula automaticamente
y se usa para ajustar el balance hidrico FAO-56.
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class RiegoModel(Base):
    __tablename__ = 'riegos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actividad_id = Column(UUID(as_uuid=True), ForeignKey('actividades.id'), nullable=False, unique=True)
    tipo_riego = Column(String(50), nullable=False)
    duracion_horas = Column(Float, nullable=True)
    porcentaje_parcela_regada = Column(Float, default=100)
    aporte_hidrico_estimado_mm = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())