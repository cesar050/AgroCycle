from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


# Categorías válidas de gasto agrícola.
# Coinciden con el CHECK constraint de la tabla compras en PostgreSQL.
CATEGORIAS_VALIDAS = {
    'semillas',
    'fertilizantes',
    'agroquimicos',
    'mano_obra',
    'otros'
}


@dataclass
class Compra:
    """
    Representa un gasto o compra realizada durante una temporada agrícola.

    Una compra puede estar vinculada opcionalmente a una actividad
    agronómica específica (ejemplo: la compra del fertilizante
    vinculada al registro de fertilización del 15 de enero).
    """
    temporada_id: str
    categoria: str
    cantidad: float
    precio_unitario: float
    costo_total: float
    fecha_compra: date

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actividad_id: Optional[str] = None
    insumo_id: Optional[int] = None
    producto_personalizado: Optional[str] = None
    unidad_medida: Optional[str] = None
    proveedor: Optional[str] = None
    registrado_por: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """
        Valida la categoría al momento de crear la entidad.
        Falla rápido antes de llegar a la base de datos.
        """
        if self.categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(
                f"Categoría '{self.categoria}' no válida. "
                f"Use: {', '.join(sorted(CATEGORIAS_VALIDAS))}"
            )

    def calcular_costo_total(self) -> float:
        """
        Recalcula el costo total desde cantidad y precio unitario.
        Útil para verificar consistencia antes de guardar.
        """
        return round(self.cantidad * self.precio_unitario, 2)

    def es_de_temporada(self, temporada_id: str) -> bool:
        """Verifica que la compra pertenece a la temporada indicada."""
        return self.temporada_id == temporada_id