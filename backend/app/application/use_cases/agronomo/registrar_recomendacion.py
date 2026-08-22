"""
CU-AGR-004 — Registrar recomendación agronómica al agricultor.

El agrónomo envía una recomendación técnica al agricultor
indicando qué acción debe tomar y con qué urgencia.
El agricultor la recibe como notificación en su panel.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.recomendacion_agronomica import RecomendacionAgronomica
from app.domain.repositories.i_recomendacion_repository import IRecomendacionRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarRecomendacionUseCase:
    """
    Implementa CU-AGR-004.

    Responsabilidades:
    1. Verificar vinculación del agrónomo a la temporada
    2. Crear y persistir la recomendación
    3. Las recomendaciones urgentes se destacan en el dashboard
    """

    def __init__(
        self,
        db: Session,
        recomendacion_repo: IRecomendacionRepository,
    ):
        self.db = db
        self.recomendacion_repo = recomendacion_repo

    @log_caso_de_uso('CU-AGR-004 Registrar Recomendación')
    def ejecutar(
        self,
        agronomo_usuario_id: str,
        temporada_id: str,
        descripcion: str,
        urgencia: str,
        fecha: date,
        tipo: Optional[str] = None,
        temporada_parcela_id: Optional[str] = None,
        fecha_limite: Optional[date] = None,
    ) -> tuple:
        """
        Registra una recomendación agronómica para el agricultor.

        Args:
            agronomo_usuario_id: UUID del usuario agrónomo autenticado
            temporada_id: UUID de la temporada
            descripcion: texto de la recomendación
            urgencia: alta, media o baja
            fecha: fecha de la recomendación
            tipo: categoría de la recomendación, opcional
            temporada_parcela_id: parcela específica, opcional
            fecha_limite: fecha límite para implementar, opcional

        Returns:
            tuple (dict, int) con resultado y código HTTP
        """
        # 1. Obtener perfil del agrónomo
        agronomo = self._obtener_agronomo(agronomo_usuario_id)

        if not agronomo:
            return {
                'error': 'Perfil de agrónomo no encontrado'
            }, 404

        # 2. Verificar vinculación a la temporada
        vinculado = self._verificar_vinculacion(
            agronomo['id'], temporada_id
        )

        if not vinculado:
            return {
                'error': 'No está vinculado a esta temporada.'
            }, 403

        # 3. Crear entidad — validación de urgencia en __post_init__
        try:
            recomendacion = RecomendacionAgronomica(
                agronomo_id=agronomo['id'],
                temporada_id=temporada_id,
                descripcion=descripcion,
                urgencia=urgencia,
                fecha=fecha,
                tipo=tipo,
                temporada_parcela_id=temporada_parcela_id,
                fecha_limite=fecha_limite,
            )
        except ValueError as e:
            return {'error': str(e)}, 400

        # 4. Persistir
        recomendacion_guardada = self.recomendacion_repo.guardar(recomendacion)

        return {
            'id': recomendacion_guardada.id,
            'agronomo_id': recomendacion_guardada.agronomo_id,
            'temporada_id': recomendacion_guardada.temporada_id,
            'temporada_parcela_id': recomendacion_guardada.temporada_parcela_id,
            'tipo': recomendacion_guardada.tipo,
            'descripcion': recomendacion_guardada.descripcion,
            'urgencia': recomendacion_guardada.urgencia,
            'es_urgente': recomendacion_guardada.es_urgente(),
            'fecha': str(recomendacion_guardada.fecha),
            'fecha_limite': str(recomendacion_guardada.fecha_limite) if recomendacion_guardada.fecha_limite else None,
            'mensaje': 'Recomendación registrada correctamente',
        }, 201

    def _obtener_agronomo(self, usuario_id: str) -> Optional[dict]:
        """Obtiene el perfil del agrónomo desde el usuario autenticado."""
        row = self.db.execute(
            text("""
                SELECT a.id, a.numero_registro
                FROM agronomos a
                WHERE a.usuario_id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        ).fetchone()

        if not row:
            return None

        return {'id': str(row.id), 'numero_registro': row.numero_registro}

    def _verificar_vinculacion(
        self, agronomo_id: str, temporada_id: str
    ) -> Optional[dict]:
        """Verifica vinculación agrónomo → finca → temporada."""
        row = self.db.execute(
            text("""
                SELECT t.id, t.estado
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

        return {'id': str(row.id), 'estado': row.estado}