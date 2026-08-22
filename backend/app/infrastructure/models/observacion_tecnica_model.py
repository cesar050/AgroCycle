from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class ObservacionTecnicaModel(Base):
    __tablename__ = 'observaciones_tecnicas'

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
    # Nullable porque una observación puede ser general
    # para toda la temporada sin apuntar a una parcela específica
    temporada_parcela_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporada_parcelas.id'),
        nullable=True
    )
    tipo = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )