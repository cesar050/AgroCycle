from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class ResultadoFinancieroModel(Base):
    __tablename__ = 'resultados_financieros'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temporada_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporadas.id'),
        nullable=False,
        unique=True  # Una temporada tiene exactamente un resultado financiero
    )
    ingresos_totales = Column(Float, default=0.0)
    costos_totales = Column(Float, default=0.0)
    costo_semillas = Column(Float, default=0.0)
    costo_fertilizantes = Column(Float, default=0.0)
    costo_agroquimicos = Column(Float, default=0.0)
    costo_mano_obra = Column(Float, default=0.0)
    costo_otros = Column(Float, default=0.0)
    ganancia_neta = Column(Float, nullable=True)
    margen_rentabilidad_porcentaje = Column(Float, nullable=True)
    costo_por_quintal = Column(Float, nullable=True)
    precio_venta_promedio_qq = Column(Float, nullable=True)
    produccion_total_qq = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )