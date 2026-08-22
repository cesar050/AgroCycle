"""
Modelo ORM de Fertilizacion para SQLAlchemy.
Detalle especifico de una actividad de fertilizacion.
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class FertilizacionModel(Base):
    __tablename__ = 'fertilizaciones'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actividad_id = Column(UUID(as_uuid=True), ForeignKey('actividades.id'), nullable=False, unique=True)
    insumo_id = Column(Integer, nullable=True)
    insumo_personalizado = Column(String(200), nullable=True)
    dosis_kg_ha = Column(Float, nullable=False)
    metodo_aplicacion = Column(String(100), nullable=True)
    costo_unitario = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())