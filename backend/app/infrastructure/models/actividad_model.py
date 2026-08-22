"""
Modelo ORM de Actividad para SQLAlchemy.
Una actividad es cualquier labor realizada en la parcela
durante la temporada: siembra, riego, fertilizacion, etc.
"""
from sqlalchemy import Column, String, Integer, DateTime, Date, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class ActividadModel(Base):
    __tablename__ = 'actividades'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temporada_id = Column(UUID(as_uuid=True), ForeignKey('temporadas.id'), nullable=False)
    temporada_parcela_id = Column(UUID(as_uuid=True), ForeignKey('temporada_parcelas.id'), nullable=True)
    tipo_actividad_id = Column(Integer, ForeignKey('tipos_actividad.id'), nullable=False)
    fecha = Column(Date, nullable=False)
    descripcion = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    costo_total = Column(Float, default=0)
    registrado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())