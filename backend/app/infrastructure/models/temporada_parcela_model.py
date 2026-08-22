"""
Modelo ORM de TemporadaParcela para SQLAlchemy.
Representa la siembra en una parcela especifica dentro de una temporada.
"""
from sqlalchemy import Column, String, Integer, DateTime, Date, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class TemporadaParcelaModel(Base):
    __tablename__ = 'temporada_parcelas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temporada_id = Column(UUID(as_uuid=True), ForeignKey('temporadas.id'), nullable=False)
    parcela_id = Column(UUID(as_uuid=True), ForeignKey('parcelas.id'), nullable=False)
    variedad_semilla_id = Column(Integer, ForeignKey('variedades_semilla.id'), nullable=True)
    fecha_siembra = Column(Date, nullable=True)
    densidad_siembra_kg_ha = Column(Float, nullable=True)
    cantidad_semilla_kg = Column(Float, nullable=True)
    estado_fenologico = Column(String(50), default='pre_siembra')
    dias_desde_siembra = Column(Integer, nullable=True)
    avance_ciclo_porcentaje = Column(Float, nullable=True)
    produccion_real_qq = Column(Float, nullable=True)
    fecha_cosecha = Column(Date, nullable=True)
    precio_venta_qq = Column(Float, nullable=True)
    volumen_vendido_qq = Column(Float, nullable=True)
    ingresos_totales = Column(Float, nullable=True)
    produccion_autoconsumo_qq = Column(Float, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())