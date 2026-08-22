"""
CU-AGR-003 — Registrar observación técnica del agrónomo.

El agrónomo anota lo que observa en campo durante su visita
o seguimiento remoto. Puede ser sobre el estado del cultivo,
el suelo o las condiciones generales de la parcela.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.observacion_tecnica import ObservacionTecnica
from app.domain.repositories.i_observacion_repository import IObservacionRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarObservacionUseCase:
    """
    Implementa CU-AGR-003.

    Responsabilidades:
    1. Verificar que el agrónomo está vinculado a la temporada
    2. Verificar que la temporada está activa
    3. Crear y persistir la observación técnica
    """

    def __init__(
        self,
        db: Session,
        observacion_repo: IObservacionRepository,
    ):
        self.db = db
        self.observacion_repo = observacion_repo

    @log_caso_de_uso('CU-AGR-003 Registrar Observación Técnica')
    def ejecutar(
        self,
        agronomo_usuario_id: str,
        temporada_id: str,
        tipo: str,
        descripcion: str,
        fecha: date,
        temporada_parcela_id: Optional[str] = None,
    ) -> tuple:
        """
        Registra una observación técnica del agrónomo.

        Args:
            agronomo_usuario_id: UUID del usuario agrónomo autenticado
            temporada_id: UUID de la temporada donde se registra
            tipo: cultivo, suelo o condiciones_generales
            descripcion: texto detallado de la observación
            fecha: fecha en que se realizó la observación
            temporada_parcela_id: opcional, parcela específica

        Returns:
            tuple (dict, int) con resultado y código HTTP
        """
        # 1. Obtener el perfil del agrónomo desde el usuario autenticado
        agronomo = self._obtener_agronomo(agronomo_usuario_id)

        if not agronomo:
            return {
                'error': 'Perfil de agrónomo no encontrado para este usuario'
            }, 404

        # 2. Verificar que el agrónomo está vinculado a la temporada
        vinculado = self._verificar_vinculacion(
            agronomo['id'], temporada_id
        )

        if not vinculado:
            return {
                'error': 'No está vinculado a esta temporada. '
                         'El agricultor debe vincularlo primero.'
            }, 403

        # 3. Verificar que la temporada está activa
        if vinculado['estado'] != 'activa':
            return {
                'error': f"No se pueden registrar observaciones en una "
                         f"temporada {vinculado['estado']}."
            }, 400

        # 4. Crear entidad — validación de tipo en __post_init__
        try:
            observacion = ObservacionTecnica(
                agronomo_id=agronomo['id'],
                temporada_id=temporada_id,
                tipo=tipo,
                descripcion=descripcion,
                fecha=fecha,
                temporada_parcela_id=temporada_parcela_id,
            )
        except ValueError as e:
            return {'error': str(e)}, 400

        # 5. Persistir
        observacion_guardada = self.observacion_repo.guardar(observacion)

        return {
            'id': observacion_guardada.id,
            'agronomo_id': observacion_guardada.agronomo_id,
            'temporada_id': observacion_guardada.temporada_id,
            'temporada_parcela_id': observacion_guardada.temporada_parcela_id,
            'tipo': observacion_guardada.tipo,
            'descripcion': observacion_guardada.descripcion,
            'fecha': str(observacion_guardada.fecha),
            'es_general': observacion_guardada.es_general(),
            'mensaje': 'Observación técnica registrada correctamente',
        }, 201

    def _obtener_agronomo(self, usuario_id: str) -> Optional[dict]:
        """
        Obtiene el perfil del agrónomo desde el usuario autenticado.
        El JWT guarda el usuario_id — necesitamos el agronomo_id
        para vincularlo a la observación.
        """
        row = self.db.execute(
            text("""
                SELECT a.id, a.numero_registro, a.especialidad
                FROM agronomos a
                WHERE a.usuario_id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'numero_registro': row.numero_registro,
            'especialidad': row.especialidad,
        }

    def _verificar_vinculacion(
        self, agronomo_id: str, temporada_id: str
    ) -> Optional[dict]:
        """
        Verifica que el agrónomo está vinculado a la finca
        de la temporada indicada y obtiene el estado de la temporada.

        Un agrónomo se vincula a una finca, no directamente a una
        temporada. La verificación recorre: temporada → finca → vinculación.
        """
        row = self.db.execute(
            text("""
                SELECT t.id, t.estado, t.nombre
                FROM temporadas t
                JOIN finca_agronomo fa ON t.finca_id = fa.finca_id
                WHERE t.id = CAST(:temporada_id AS uuid)
                  AND fa.agronomo_id = CAST(:agronomo_id AS uuid)
                  AND fa.activo = true
            """),
            {
                'temporada_id': temporada_id,
                'agronomo_id': agronomo_id,
            }
        ).fetchone()

        if not row:
            return None

        return {
            'id': str(row.id),
            'estado': row.estado,
            'nombre': row.nombre,
        }