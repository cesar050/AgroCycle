from sqlalchemy import (
    Column, String, Integer, Float, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class EstimacionModel(Base):
    __tablename__ = 'estimaciones_produccion'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temporada_parcela_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporada_parcelas.id', ondelete='CASCADE'),
        nullable=False
    )
    # Sin FK a versiones_modelo por ahora — se agrega cuando
    # se implemente el módulo de versiones del modelo ML
    version_modelo_id = Column(Integer, nullable=True)
    fecha_generacion = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    valor_qq_ha = Column(Float, nullable=False)
    valor_total_qq = Column(Float, nullable=True)
    margen_error_porcentaje = Column(Float, nullable=True)
    valor_minimo_qq_ha = Column(Float, nullable=True)
    valor_maximo_qq_ha = Column(Float, nullable=True)
    etapa_fenologica_momento = Column(String(50), nullable=True)
    dias_desde_siembra_momento = Column(Integer, nullable=True)
    algoritmo_usado = Column(
        SAEnum(
            'fao33', 'ridge', 'random_forest',
            'gradient_boosting', 'ensemble',
            name='algoritmo_estimacion_enum'
        ),
        nullable=False
    )
    variables_entrada = Column(JSONB, nullable=True)
    factores_positivos = Column(JSONB, nullable=True)
    factores_negativos = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    temporada_parcela = relationship('TemporadaParcelaModel')