from sqlalchemy import Column, BigInteger, Date, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class IndicadorEstresModel(Base):
    __tablename__ = 'indicadores_estres_hidrico'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    temporada_parcela_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporada_parcelas.id', ondelete='CASCADE'),
        nullable=False
    )
    fecha = Column(Date, nullable=False)
    nivel_estres = Column(String(20), nullable=False)
    valor_ks = Column(Float, nullable=True)
    requerimiento_hidrico_etapa_mm = Column(Float, nullable=True)
    humedad_disponible_mm = Column(Float, nullable=True)
    dias_hasta_estres_critico = Column(Integer, nullable=True)
    estado_fenologico = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())