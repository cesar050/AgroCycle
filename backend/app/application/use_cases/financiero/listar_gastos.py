"""
CU-FIN-003 — Ver presupuesto vs gasto real de la temporada.

Permite al agricultor ver en cualquier momento cuánto ha gastado,
desglosado por categoría y comparado con el total acumulado.
Es el panel de control financiero durante la temporada activa.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.repositories.i_compra_repository import ICompraRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class ListarGastosUseCase:
    """
    Implementa CU-FIN-003.

    Responsabilidades:
    1. Listar todas las compras de la temporada cronológicamente
    2. Mostrar totales agrupados por categoría
    3. Mostrar el acumulado total gastado hasta la fecha
    """

    def __init__(
        self,
        db: Session,
        compra_repo: ICompraRepository,
    ):
        self.db = db
        self.compra_repo = compra_repo

    @log_caso_de_uso('CU-FIN-003 Listar Gastos')
    def ejecutar(
        self,
        temporada_id: str,
        agricultor_id: str,
        categoria: str = None,
    ) -> tuple:
        """
        Retorna el listado de gastos y resumen financiero de la temporada.

        Args:
            temporada_id: UUID de la temporada
            agricultor_id: UUID del usuario para verificar pertenencia
            categoria: filtro opcional por categoría de gasto

        Returns:
            tuple (dict, int) con gastos y resumen, código HTTP
        """
        # 1. Verificar pertenencia
        temporada = self._obtener_temporada(temporada_id, agricultor_id)

        if not temporada:
            return {
                'error': 'Temporada no encontrada o no pertenece al agricultor'
            }, 404

        # 2. Obtener compras — todas o filtradas por categoría
        if categoria:
            compras = self.compra_repo.listar_por_categoria(
                temporada_id, categoria
            )
        else:
            compras = self.compra_repo.listar_por_temporada(temporada_id)

        # 3. Obtener totales por categoría siempre completos
        totales = self.compra_repo.total_por_categoria(temporada_id)

        return {
            'temporada': {
                'id': temporada['id'],
                'nombre': temporada['nombre'],
                'estado': temporada['estado'],
            },
            'filtro_categoria': categoria,
            'resumen': {
                'total_gastado': totales['total'],
                'por_categoria': {
                    'semillas': totales['semillas'],
                    'fertilizantes': totales['fertilizantes'],
                    'agroquimicos': totales['agroquimicos'],
                    'mano_obra': totales['mano_obra'],
                    'otros': totales['otros'],
                },
            },
            'total_compras': len(compras),
            'compras': [
                {
                    'id': c.id,
                    'categoria': c.categoria,
                    'producto': c.producto_personalizado,
                    'insumo_id': c.insumo_id,
                    'cantidad': c.cantidad,
                    'unidad_medida': c.unidad_medida,
                    'precio_unitario': c.precio_unitario,
                    'costo_total': c.costo_total,
                    'fecha_compra': str(c.fecha_compra),
                    'proveedor': c.proveedor,
                    'actividad_id': c.actividad_id,
                }
                for c in compras
            ],
        }, 200

    def _obtener_temporada(
        self, temporada_id: str, agricultor_id: str
    ) -> dict:
        """Verifica que la temporada pertenece al agricultor."""
        row = self.db.execute(
            text("""
                SELECT t.id, t.nombre, t.estado
                FROM temporadas t
                JOIN agricultores a ON t.agricultor_id = a.id
                WHERE t.id = CAST(:temporada_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'temporada_id': temporada_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'nombre': row.nombre,
            'estado': row.estado,
        }