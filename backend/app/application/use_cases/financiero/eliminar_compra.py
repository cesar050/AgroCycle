"""
CU-FIN-007 — Eliminar una compra registrada por error.

Permite al agricultor corregir errores de registro eliminando
una compra. Solo se puede eliminar si la temporada está activa
y la compra pertenece al agricultor.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.repositories.i_compra_repository import ICompraRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class EliminarCompraUseCase:
    """
    Implementa eliminación de compra con verificación de pertenencia.

    No hace soft delete — elimina directamente porque una compra
    errónea no debe afectar los cálculos de rentabilidad.
    """

    def __init__(
        self,
        db: Session,
        compra_repo: ICompraRepository,
    ):
        self.db = db
        self.compra_repo = compra_repo

    @log_caso_de_uso('CU-FIN Eliminar Compra')
    def ejecutar(
        self,
        compra_id: str,
        agricultor_id: str,
    ) -> tuple:
        """
        Elimina una compra verificando que pertenece al agricultor
        y que la temporada está activa.

        Args:
            compra_id: UUID de la compra a eliminar
            agricultor_id: UUID del usuario para verificar pertenencia

        Returns:
            tuple (dict, int) con mensaje y código HTTP
        """
        # 1. Verificar que la compra existe y pertenece al agricultor
        compra_data = self._verificar_pertenencia(compra_id, agricultor_id)

        if not compra_data:
            return {
                'error': 'Compra no encontrada o no pertenece al agricultor'
            }, 404

        # 2. Verificar que la temporada está activa
        if compra_data['estado_temporada'] != 'activa':
            return {
                'error': 'No se pueden eliminar compras de una temporada '
                         f"{compra_data['estado_temporada']}."
            }, 400

        # 3. Eliminar
        eliminada = self.compra_repo.eliminar(compra_id)

        if not eliminada:
            return {'error': 'No se pudo eliminar la compra'}, 500

        return {
            'mensaje': 'Compra eliminada correctamente',
            'compra_id': compra_id,
        }, 200

    def _verificar_pertenencia(
        self, compra_id: str, agricultor_id: str
    ) -> dict:
        """
        Verifica en una sola query que la compra existe,
        pertenece al agricultor y obtiene el estado de la temporada.
        """
        row = self.db.execute(
            text("""
                SELECT
                    c.id,
                    c.costo_total,
                    t.estado AS estado_temporada
                FROM compras c
                JOIN temporadas t ON c.temporada_id = t.id
                JOIN agricultores a ON t.agricultor_id = a.id
                WHERE c.id = CAST(:compra_id AS uuid)
                  AND a.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'compra_id': compra_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'costo_total': float(row.costo_total),
            'estado_temporada': row.estado_temporada,
        }