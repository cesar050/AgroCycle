from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from sqlalchemy import Float
from app.infrastructure.database import Base
import uuid


class FincaModel(Base):
    __tablename__ = 'fincas'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agricultor_id = Column(UUID(as_uuid=True), ForeignKey('agricultores.id'), nullable=False)
    nombre = Column(String(150), nullable=False)
    provincia = Column(String(100), nullable=True)
    canton = Column(String(100), nullable=True)
    parroquia = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    geometria = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True)
    superficie_ha = Column(Float, nullable=True)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )