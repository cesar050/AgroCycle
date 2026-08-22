from sqlalchemy import Column, String, Date, DateTime, Boolean, Float, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class EvaluacionCampoModel(Base):
    __tablename__ = 'evaluaciones_campo'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agronomo_id = Column(
        UUID(as_uuid=True),
        ForeignKey('agronomos.id'),
        nullable=False
    )
    temporada_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporadas.id'),
        nullable=False
    )
    temporada_parcela_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporada_parcelas.id'),
        nullable=True
    )
    fecha = Column(Date, nullable=False)
    densidad_plantas_ha = Column(Integer, nullable=True)
    incidencia_plagas_porcentaje = Column(Float, nullable=True)
    incidencia_enfermedades_porcentaje = Column(Float, nullable=True)
    estado_nutricional = Column(String(50), nullable=True)
    estado_fenologico_confirmado = Column(String(50), nullable=True)
    observaciones = Column(Text, nullable=True)
    # Se activa automáticamente si requiere_alerta() es True
    # al momento de registrar la evaluación
    alerta_generada = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())