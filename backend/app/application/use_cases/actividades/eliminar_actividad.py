"""
CU-ACT-007 — Eliminar actividad (soft delete).

No elimina el registro físicamente de la BD.
Marca activo=False para mantener el historial
y no afectar cálculos financieros previos.

Un riego eliminado no debe desaparecer del historial
de costos si ya fue contabilizado en la rentabilidad.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso
from app.infrastructure.transaction import transaccion_atomica


class EliminarActividadUseCase:
    """
    Implementa CU-ACT-007.

    Responsabilidades:
    1. Verificar que la actividad pertenece al agricultor
    2. Verificar que la temporada está activa
    3. Marcar activo=False en actividades y su tabla hija
    """

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('CU-ACT-007 Eliminar Actividad')
    def ejecutar(
        self,
        actividad_id: str,
        agricultor_id: str,
    ) -> tuple:
        """
        Realiza el soft delete de una actividad.

        Args:
            actividad_id: UUID de la actividad a eliminar
            agricultor_id: UUID del usuario autenticado

        Returns:
            tuple (dict resultado, int código HTTP)
        """
        # 1. Verificar pertenencia y estado de temporada
        actividad = self._obtener_actividad(actividad_id, agricultor_id)

        if not actividad:
            return {
                'error': 'Actividad no encontrada o no pertenece al agricultor.'
            }, 404

        if not actividad['activo']:
            return {
                'error': 'La actividad ya fue eliminada anteriormente.'
            }, 400

        if actividad['temporada_estado'] != 'activa':
            return {
                'error': f"No se pueden eliminar actividades de una temporada "
                         f"{actividad['temporada_estado']}."
            }, 400

        # 2. Soft delete en transacción atómica
        try:
            with transaccion_atomica(self.db):
                self.db.execute(
                    text("""
                        UPDATE actividades
                        SET activo = FALSE,
                            updated_at = NOW()
                        WHERE id = CAST(:actividad_id AS uuid)
                    """),
                    {'actividad_id': actividad_id}
                )
        except Exception as e:
            return {
                'error': f'Error al eliminar la actividad: {str(e)}'
            }, 500

        return {
            'actividad_id': actividad_id,
            'tipo': actividad['tipo'],
            'fecha': actividad['fecha'],
            'costo_total': actividad['costo_total'],
            'mensaje': f"Actividad de {actividad['tipo']} del "
                       f"{actividad['fecha']} eliminada correctamente. "
                       f"El registro se mantiene en el historial.",
        }, 200

    def _obtener_actividad(
        self, actividad_id: str, agricultor_id: str
    ) -> dict:
        """
        Obtiene la actividad verificando pertenencia al agricultor
        y estado de la temporada en una sola query.
        """
        row = self.db.execute(
            text("""
                SELECT
                    a.id,
                    a.fecha,
                    a.costo_total,
                    a.activo,
                    ta.nombre       AS tipo,
                    t.estado        AS temporada_estado
                FROM actividades a
                JOIN tipos_actividad ta ON a.tipo_actividad_id = ta.id
                JOIN temporadas t       ON a.temporada_id = t.id
                JOIN agricultores ag    ON t.agricultor_id = ag.id
                WHERE a.id = CAST(:actividad_id AS uuid)
                  AND ag.usuario_id = CAST(:agricultor_id AS uuid)
            """),
            {
                'actividad_id': actividad_id,
                'agricultor_id': agricultor_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'fecha': str(row.fecha),
            'costo_total': float(row.costo_total or 0),
            'activo': row.activo,
            'tipo': row.tipo,
            'temporada_estado': row.temporada_estado,
        }