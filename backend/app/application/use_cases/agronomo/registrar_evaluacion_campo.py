"""
CU-AGR-007 — Registrar evaluación de campo presencial.

El agrónomo registra datos observacionales directos de la parcela
que los sensores y APIs no pueden capturar. Si detecta problemas
críticos el sistema genera una alerta automática al agricultor.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.entities.evaluacion_campo import EvaluacionCampo
from app.domain.repositories.i_evaluacion_campo_repository import IEvaluacionCampoRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarEvaluacionCampoUseCase:
    """
    Implementa CU-AGR-007.

    Responsabilidades:
    1. Verificar vinculación del agrónomo
    2. Crear la evaluación con detección automática de alertas
    3. Persistir y retornar resultado con indicación de alerta
    """

    def __init__(
        self,
        db: Session,
        evaluacion_repo: IEvaluacionCampoRepository,
    ):
        self.db = db
        self.evaluacion_repo = evaluacion_repo

    @log_caso_de_uso('CU-AGR-007 Registrar Evaluación de Campo')
    def ejecutar(
        self,
        agronomo_usuario_id: str,
        temporada_id: str,
        fecha: date,
        temporada_parcela_id: Optional[str] = None,
        densidad_plantas_ha: Optional[int] = None,
        incidencia_plagas_porcentaje: Optional[float] = None,
        incidencia_enfermedades_porcentaje: Optional[float] = None,
        estado_nutricional: Optional[str] = None,
        estado_fenologico_confirmado: Optional[str] = None,
        observaciones: Optional[str] = None,
    ) -> tuple:
        """
        Registra una evaluación de campo con detección automática de alertas.

        Si la incidencia de plagas o enfermedades supera el 20%
        o el estado nutricional es deficiente, el sistema activa
        una alerta automática para el agricultor.

        Returns:
            tuple (dict, int) con resultado y código HTTP
        """
        # 1. Obtener perfil del agrónomo
        agronomo = self._obtener_agronomo(agronomo_usuario_id)

        if not agronomo:
            return {
                'error': 'Perfil de agrónomo no encontrado'
            }, 404

        # 2. Verificar vinculación
        vinculado = self._verificar_vinculacion(
            agronomo['id'], temporada_id
        )

        if not vinculado:
            return {
                'error': 'No está vinculado a esta temporada.'
            }, 403

        # 3. Crear entidad — validación de estado nutricional en __post_init__
        try:
            evaluacion = EvaluacionCampo(
                agronomo_id=agronomo['id'],
                temporada_id=temporada_id,
                fecha=fecha,
                temporada_parcela_id=temporada_parcela_id,
                densidad_plantas_ha=densidad_plantas_ha,
                incidencia_plagas_porcentaje=incidencia_plagas_porcentaje,
                incidencia_enfermedades_porcentaje=incidencia_enfermedades_porcentaje,
                estado_nutricional=estado_nutricional,
                estado_fenologico_confirmado=estado_fenologico_confirmado,
                observaciones=observaciones,
            )
        except ValueError as e:
            return {'error': str(e)}, 400

        # 4. Detectar si requiere alerta automática
        evaluacion.alerta_generada = evaluacion.requiere_alerta()

        # 5. Persistir
        evaluacion_guardada = self.evaluacion_repo.guardar(evaluacion)

        return {
            'id': evaluacion_guardada.id,
            'agronomo_id': evaluacion_guardada.agronomo_id,
            'temporada_id': evaluacion_guardada.temporada_id,
            'temporada_parcela_id': evaluacion_guardada.temporada_parcela_id,
            'fecha': str(evaluacion_guardada.fecha),
            'densidad_plantas_ha': evaluacion_guardada.densidad_plantas_ha,
            'incidencia_plagas_porcentaje': evaluacion_guardada.incidencia_plagas_porcentaje,
            'incidencia_enfermedades_porcentaje': evaluacion_guardada.incidencia_enfermedades_porcentaje,
            'estado_nutricional': evaluacion_guardada.estado_nutricional,
            'estado_fenologico_confirmado': evaluacion_guardada.estado_fenologico_confirmado,
            'observaciones': evaluacion_guardada.observaciones,
            'alerta_generada': evaluacion_guardada.alerta_generada,
            'mensaje': (
                'Evaluación registrada. ALERTA: Se detectaron condiciones críticas. '
                'El agricultor ha sido notificado.'
                if evaluacion_guardada.alerta_generada
                else 'Evaluación de campo registrada correctamente.'
            ),
        }, 201

    def _obtener_agronomo(self, usuario_id: str) -> Optional[dict]:
        """Obtiene el perfil del agrónomo desde el usuario autenticado."""
        row = self.db.execute(
            text("""
                SELECT a.id
                FROM agronomos a
                WHERE a.usuario_id = CAST(:usuario_id AS uuid)
            """),
            {'usuario_id': usuario_id}
        ).fetchone()

        if not row:
            return None

        return {'id': str(row.id)}

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