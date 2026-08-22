from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.entities.compra import Compra
from app.domain.repositories.i_compra_repository import ICompraRepository
from app.infrastructure.models.compra_model import CompraModel
import uuid


class PgCompraRepository(ICompraRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, compra: Compra) -> Compra:
        """Persiste una nueva compra en la base de datos."""
        modelo = CompraModel(
            id=uuid.UUID(compra.id),
            temporada_id=uuid.UUID(compra.temporada_id),
            actividad_id=uuid.UUID(compra.actividad_id) if compra.actividad_id else None,
            insumo_id=compra.insumo_id,
            producto_personalizado=compra.producto_personalizado,
            categoria=compra.categoria,
            cantidad=compra.cantidad,
            unidad_medida=compra.unidad_medida,
            precio_unitario=compra.precio_unitario,
            costo_total=compra.costo_total,
            fecha_compra=compra.fecha_compra,
            proveedor=compra.proveedor,
            registrado_por=uuid.UUID(compra.registrado_por) if compra.registrado_por else None,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def guardar_en_sesion(self, compra: Compra) -> CompraModel:
        """
        Agrega la compra a la sesión sin hacer commit.
        Usar cuando la operación forma parte de una transacción
        atómica con otras operaciones relacionadas.
        El commit lo maneja el context manager transaccion_atomica.
        """
        modelo = CompraModel(
            id=uuid.UUID(compra.id),
            temporada_id=uuid.UUID(compra.temporada_id),
            actividad_id=uuid.UUID(compra.actividad_id) if compra.actividad_id else None,
            insumo_id=compra.insumo_id,
            producto_personalizado=compra.producto_personalizado,
            categoria=compra.categoria,
            cantidad=compra.cantidad,
            unidad_medida=compra.unidad_medida,
            precio_unitario=compra.precio_unitario,
            costo_total=compra.costo_total,
            fecha_compra=compra.fecha_compra,
            proveedor=compra.proveedor,
            registrado_por=uuid.UUID(compra.registrado_por) if compra.registrado_por else None,
        )
        self.db.add(modelo)
        return modelo

    def obtener_por_id(self, compra_id: str) -> Optional[Compra]:
        """Busca una compra por su UUID."""
        modelo = self.db.query(CompraModel).filter(
            CompraModel.id == uuid.UUID(compra_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def listar_por_temporada(self, temporada_id: str) -> List[Compra]:
        """
        Retorna todas las compras de una temporada ordenadas por fecha.
        Orden ascendente para ver la cronología del gasto.
        """
        modelos = self.db.query(CompraModel).filter(
            CompraModel.temporada_id == uuid.UUID(temporada_id)
        ).order_by(CompraModel.fecha_compra.asc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def listar_por_categoria(
        self, temporada_id: str, categoria: str
    ) -> List[Compra]:
        """Retorna compras filtradas por categoría de gasto."""
        modelos = self.db.query(CompraModel).filter(
            CompraModel.temporada_id == uuid.UUID(temporada_id),
            CompraModel.categoria == categoria
        ).order_by(CompraModel.fecha_compra.asc()).all()
        return [self._modelo_a_entidad(m) for m in modelos]

    def total_por_categoria(self, temporada_id: str) -> dict:
        """
        Calcula el total gastado por categoría usando GROUP BY en BD.
        Más eficiente que traer todos los registros y sumar en Python
        cuando hay muchas compras acumuladas en la temporada.
        """
        sql = text("""
            SELECT
                categoria,
                SUM(costo_total) AS total
            FROM compras
            WHERE temporada_id = CAST(:temporada_id AS uuid)
            GROUP BY categoria
        """)
        rows = self.db.execute(
            sql, {'temporada_id': temporada_id}
        ).fetchall()

        # Inicializar todas las categorías en 0
        # para que siempre aparezcan aunque no haya compras
        totales = {
            'semillas': 0.0,
            'fertilizantes': 0.0,
            'agroquimicos': 0.0,
            'mano_obra': 0.0,
            'otros': 0.0,
        }

        for row in rows:
            totales[row.categoria] = round(float(row.total), 2)

        totales['total'] = round(sum(totales.values()), 2)
        return totales

    def eliminar(self, compra_id: str) -> bool:
        """
        Elimina una compra por su UUID.
        Retorna True si se eliminó, False si no existía.
        """
        modelo = self.db.query(CompraModel).filter(
            CompraModel.id == uuid.UUID(compra_id)
        ).first()

        if not modelo:
            return False

        self.db.delete(modelo)
        self.db.commit()
        return True

    def _modelo_a_entidad(self, m: CompraModel) -> Compra:
        """
        Convierte el modelo ORM a entidad de dominio.
        Aísla la capa de infraestructura del dominio —
        si cambia el modelo, solo cambia este método.
        """
        return Compra(
            id=str(m.id),
            temporada_id=str(m.temporada_id),
            actividad_id=str(m.actividad_id) if m.actividad_id else None,
            insumo_id=m.insumo_id,
            producto_personalizado=m.producto_personalizado,
            categoria=m.categoria,
            cantidad=float(m.cantidad),
            unidad_medida=m.unidad_medida,
            precio_unitario=float(m.precio_unitario),
            costo_total=float(m.costo_total),
            fecha_compra=m.fecha_compra,
            proveedor=m.proveedor,
            registrado_por=str(m.registrado_por) if m.registrado_por else None,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )