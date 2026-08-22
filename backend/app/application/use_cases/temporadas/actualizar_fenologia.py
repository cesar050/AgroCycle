"""
Caso de uso: CU-TEM-004 Actualizar Estado Fenologico.
Calcula y actualiza automaticamente la etapa fenologica
de todas las parcelas activas segun los dias transcurridos
desde la fecha de siembra y el ciclo vegetativo de la variedad.
Se ejecuta diariamente via Celery o manualmente por el sistema.
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('actualizar_fenologia')


class ActualizarFenologiaUseCase:
    """
    Implementa CU-TEM-004.
    Recorre todas las temporada_parcelas activas y actualiza
    su estado fenologico segun los dias desde la siembra.
    """

    ETAPAS_FENOLOGICAS = [
        (5,  'emergencia'),
        (30, 'crecimiento_vegetativo'),
        (55, 'floracion'),
        (80, 'llenado_grano'),
        (95, 'maduracion'),
        (100,'cosecha')
    ]

    def __init__(
        self,
        temporada_parcela_repository: ITemporadaParcelaRepository,
        db: Session
    ):
        self.tp_repo = temporada_parcela_repository
        self.db = db

    @log_caso_de_uso('actualizar_fenologia')
    def ejecutar(self, temporada_id: str = None) -> dict:
        """
        Actualiza la fenologia de todas las parcelas activas.
        Si se pasa temporada_id solo actualiza esa temporada.
        """
        filtro = ""
        params = {"hoy": date.today()}
        if temporada_id:
            filtro = "AND tp.temporada_id = CAST(:temporada_id AS uuid)"
            params["temporada_id"] = temporada_id

        parcelas = self.db.execute(
            text(f"""
                SELECT
                    tp.id,
                    tp.fecha_siembra,
                    tp.estado_fenologico,
                    vs.ciclo_vegetativo_dias
                FROM temporada_parcelas tp
                LEFT JOIN variedades_semilla vs ON tp.variedad_semilla_id = vs.id
                JOIN temporadas t ON tp.temporada_id = t.id
                WHERE tp.activo = true
                AND t.estado = 'activa'
                AND tp.fecha_siembra IS NOT NULL
                AND tp.fecha_siembra <= :hoy
                {filtro}
            """),
            params
        ).fetchall()

        actualizados = 0
        for p in parcelas:
            dias = (date.today() - p.fecha_siembra).days
            ciclo = p.ciclo_vegetativo_dias or 120
            porcentaje = min((dias / ciclo) * 100, 100)

            nuevo_estado = self._calcular_estado(porcentaje)

            if nuevo_estado != p.estado_fenologico:
                self.db.execute(
                    text("""
                        UPDATE temporada_parcelas
                        SET estado_fenologico = :estado,
                            dias_desde_siembra = :dias,
                            avance_ciclo_porcentaje = :porcentaje,
                            updated_at = NOW()
                        WHERE id = CAST(:tp_id AS uuid)
                    """),
                    {
                        "estado": nuevo_estado,
                        "dias": dias,
                        "porcentaje": round(porcentaje, 1),
                        "tp_id": str(p.id)
                    }
                )
                logger.info(
                    f"Fenologia actualizada: {p.id} "
                    f"{p.estado_fenologico} -> {nuevo_estado} "
                    f"(dia {dias} de {ciclo})"
                )
                actualizados += 1
            else:
                # Actualizar dias y porcentaje aunque el estado no cambie
                self.db.execute(
                    text("""
                        UPDATE temporada_parcelas
                        SET dias_desde_siembra = :dias,
                            avance_ciclo_porcentaje = :porcentaje,
                            updated_at = NOW()
                        WHERE id = CAST(:tp_id AS uuid)
                    """),
                    {
                        "dias": dias,
                        "porcentaje": round(porcentaje, 1),
                        "tp_id": str(p.id)
                    }
                )

        self.db.commit()

        logger.info(
            f"Fenologia procesada: {len(parcelas)} parcelas, "
            f"{actualizados} con cambio de estado"
        )

        return {
            "total_parcelas_procesadas": len(parcelas),
            "total_actualizadas": actualizados,
            "fecha_actualizacion": date.today().isoformat()
        }

    def _calcular_estado(self, porcentaje: float) -> str:
        """Determina la etapa fenologica segun el porcentaje del ciclo."""
        for limite, estado in self.ETAPAS_FENOLOGICAS:
            if porcentaje < limite:
                return estado
        return 'cosecha'