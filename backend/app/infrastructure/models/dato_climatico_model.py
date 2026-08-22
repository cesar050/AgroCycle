"""
Modelo ORM de DatoClimatico para SQLAlchemy.
Guarda los datos climaticos diarios por parcela
descargados de Open-Meteo API.
"""
from sqlalchemy import Column, Integer, DateTime, Date, Float, String, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class DatoClimaticoModel(Base):
    __tablename__ = 'datos_climaticos'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parcela_id = Column(UUID(as_uuid=True), ForeignKey('parcelas.id'), nullable=False)
    temporada_id = Column(UUID(as_uuid=True), ForeignKey('temporadas.id'), nullable=True)
    fecha = Column(Date, nullable=False)
    precipitacion_mm = Column(Float, nullable=True, default=0)
    temperatura_max_c = Column(Float, nullable=True)
    temperatura_min_c = Column(Float, nullable=True)
    temperatura_promedio_c = Column(Float, nullable=True)
    humedad_relativa_porcentaje = Column(Float, nullable=True)
    radiacion_solar_mj_m2 = Column(Float, nullable=True)
    velocidad_viento_km_h = Column(Float, nullable=True)
    evapotranspiracion_mm = Column(Float, nullable=True)
    fuente = Column(String(50), default='api')
    created_at = Column(DateTime(timezone=True), server_default=func.now())