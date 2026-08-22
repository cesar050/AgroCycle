from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.infrastructure.database import Base


class VariedadSemillaModel(Base):
    __tablename__ = 'variedades_semilla'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cultivo_id = Column(Integer, ForeignKey('cultivos.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    nombre_comercial = Column(String(100), nullable=True)
    ciclo_vegetativo_dias = Column(Integer, nullable=False)
    produccion_potencial_qq_ha = Column(Numeric(8, 2), nullable=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())