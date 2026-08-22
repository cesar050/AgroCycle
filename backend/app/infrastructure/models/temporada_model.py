"""
Modelo ORM de Temporada para SQLAlchemy.
Mapea la entidad Temporada a la tabla 'temporadas' de PostgreSQL.
"""
from sqlalchemy import Column, String, Integer, DateTime, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class TemporadaModel(Base):
    __tablename__ = 'temporadas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agricultor_id = Column(UUID(as_uuid=True), ForeignKey('agricultores.id'), nullable=False)
    finca_id = Column(UUID(as_uuid=True), ForeignKey('fincas.id'), nullable=False)
    cultivo_id = Column(Integer, ForeignKey('cultivos.id'), nullable=False)
    nombre = Column(String(150), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin_estimada = Column(Date, nullable=True)
    fecha_fin_real = Column(Date, nullable=True)
    estado = Column(String(20), default='activa')
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())