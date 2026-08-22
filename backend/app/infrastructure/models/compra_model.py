from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.infrastructure.database import Base
import uuid


class CompraModel(Base):
    __tablename__ = 'compras'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temporada_id = Column(
        UUID(as_uuid=True),
        ForeignKey('temporadas.id', ondelete='CASCADE'),
        nullable=False
    )
    actividad_id = Column(
        UUID(as_uuid=True),
        ForeignKey('actividades.id'),
        nullable=True
    )
    # Sin FK a insumos por ahora — tabla sin modelo registrado aún.
    # Se agrega cuando se implemente el módulo de catálogos CU-ADM-003.
    insumo_id = Column(Integer, nullable=True)
    producto_personalizado = Column(String(200), nullable=True)
    categoria = Column(
        SAEnum(
            'semillas', 'fertilizantes', 'agroquimicos',
            'mano_obra', 'otros',
            name='categoria_compra_enum'
        ),
        nullable=False
    )
    cantidad = Column(Float, nullable=False)
    unidad_medida = Column(String(20), nullable=True)
    precio_unitario = Column(Float, nullable=False)
    costo_total = Column(Float, nullable=False)
    fecha_compra = Column(Date, nullable=False)
    proveedor = Column(String(200), nullable=True)
    registrado_por = Column(
        UUID(as_uuid=True),
        ForeignKey('usuarios.id'),
        nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )