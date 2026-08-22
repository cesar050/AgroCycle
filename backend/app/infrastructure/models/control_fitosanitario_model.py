"""
Modelo ORM de ControlFitosanitario para SQLAlchemy.
Detalle especifico de una actividad de control de plagas,
enfermedades o malezas.
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class ControlFitosanitarioModel(Base):
    __tablename__ = 'controles_fitosanitarios'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actividad_id = Column(UUID(as_uuid=True), ForeignKey('actividades.id'), nullable=False, unique=True)
    tipo_control = Column(String(50), nullable=False)
    insumo_id = Column(Integer, nullable=True)
    insumo_personalizado = Column(String(200), nullable=True)
    dosis_aplicada = Column(Float, nullable=True)
    metodo_aplicacion = Column(String(100), nullable=True)
    motivo = Column(Text, nullable=True)
    incidencia_porcentaje = Column(Float, nullable=True)
    condicion_humedad_momento = Column(Float, nullable=True)
    condicion_temperatura_momento = Column(Float, nullable=True)
    efectividad_observada = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())