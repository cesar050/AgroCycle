"""
Caso de uso: Listar Actividades de una Temporada.
"""
from typing import Optional
from app.domain.repositories.i_actividad_repository import IActividadRepository
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso
from sqlalchemy import text

logger = configurar_logger('listar_actividades')


class ListarActividadesUseCase:

    def __init__(self, actividad_repository: IActividadRepository, db):
        self.actividad_repo = actividad_repository
        self.db = db

    @log_caso_de_uso('listar_actividades')
    def ejecutar(
        self,
        temporada_id: str,
        temporada_parcela_id: str = None
    ) -> list:
        """Lista todas las actividades de una temporada con detalle de riego."""
        filtro_parcela = ""
        params = {"temporada_id": temporada_id}

        if temporada_parcela_id:
            filtro_parcela = "AND a.temporada_parcela_id = CAST(:tp_id AS uuid)"
            params["tp_id"] = temporada_parcela_id

        resultados = self.db.execute(
            text(f"""
                SELECT
                    a.id, a.fecha, a.descripcion, a.observaciones,
                    a.costo_total, a.temporada_parcela_id,
                    ta.nombre as tipo_actividad,
                    ta.id as tipo_actividad_id,
                    r.tipo_riego, r.duracion_horas,
                    r.porcentaje_parcela_regada,
                    r.aporte_hidrico_estimado_mm
                FROM actividades a
                JOIN tipos_actividad ta ON a.tipo_actividad_id = ta.id
                LEFT JOIN riegos r ON r.actividad_id = a.id
                WHERE a.temporada_id = CAST(:temporada_id AS uuid)
                {filtro_parcela}
                ORDER BY a.fecha DESC
            """),
            params
        ).fetchall()

        return [
            {
                "id": str(r.id),
                "fecha": str(r.fecha),
                "tipo_actividad": r.tipo_actividad,
                "tipo_actividad_id": r.tipo_actividad_id,
                "descripcion": r.descripcion,
                "observaciones": r.observaciones,
                "costo_total": float(r.costo_total or 0),
                "temporada_parcela_id": str(r.temporada_parcela_id) if r.temporada_parcela_id else None,
                "detalle_riego": {
                    "tipo_riego": r.tipo_riego,
                    "duracion_horas": float(r.duracion_horas) if r.duracion_horas else None,
                    "porcentaje_parcela_regada": float(r.porcentaje_parcela_regada) if r.porcentaje_parcela_regada else None,
                    "aporte_hidrico_estimado_mm": float(r.aporte_hidrico_estimado_mm) if r.aporte_hidrico_estimado_mm else None
                } if r.tipo_riego else None
            }
            for r in resultados
        ]