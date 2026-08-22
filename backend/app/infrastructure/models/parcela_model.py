from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.infrastructure.database import Base
import uuid


class ParcelaModel(Base):
    __tablename__ = 'parcelas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lote_id = Column(UUID(as_uuid=True), ForeignKey('lotes.id'), nullable=False)
    nombre = Column(String(150), nullable=False)

    #Columna geoespacial - PostGis guarda el poligono real 
    # SRID 4326 es el sistema WGS84, el mismo que usa GPS y Google Maps
    geometria = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True)

    superficie_ha = Column(Float, nullable=True)
    tipo_suelo_id = Column(Integer, ForeignKey('tipos_suelo.id'), nullable=True)
    pendiente_porcentaje = Column(Float, nullable=True)
    altitud_promedio_msnm = Column(Float, nullable=True)
    altitud_minima_msnm = Column(Float, nullable=True)
    altitud_maxima_msnm = Column(Float, nullable=True)
    orientacion = Column(String(50), nullable=True)
    drenaje = Column(String(50), nullable=True)
    acceso_riego = Column(Boolean, default=False)
    tipo_riego = Column(String(50), nullable=True)
    observaciones = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
