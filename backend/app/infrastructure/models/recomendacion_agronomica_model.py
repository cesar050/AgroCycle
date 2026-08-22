from sqlalchemy import Column, String, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class RecomendacionAgronomicaModel(Base):
    __tablename__ = 'recomendaciones_agronomicas'

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
    tipo = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=False)
    urgencia = Column(String(20), nullable=False, default='media')
    fecha = Column(Date, nullable=False)
    fecha_limite = Column(Date, nullable=True)
    # leida e implementada las actualiza el agricultor
    # desde su panel cuando revisa las recomendaciones
    leida = Column(Boolean, default=False)
    implementada = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )