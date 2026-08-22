"""
Modelo ORM de ManoObra para SQLAlchemy.
Registro de jornales y trabajo en campo.
"""
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class ManoObraModel(Base):
    __tablename__ = 'mano_obra'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actividad_id = Column(UUID(as_uuid=True), ForeignKey('actividades.id'), nullable=False)
    tipo_labor = Column(String(150), nullable=False)
    numero_personas = Column(Integer, nullable=False, default=1)
    dias_trabajados = Column(Float, nullable=False)
    costo_jornal = Column(Float, nullable=False)
    costo_total = Column(Float, nullable=True)
    es_mano_obra_propia = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())