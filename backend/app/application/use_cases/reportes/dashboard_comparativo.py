"""
CU-REP-005 — Consultar Dashboard Comparativo entre Temporadas.

COMPONE, sin duplicar lógica de negocio, los indicadores clave de cada
temporada del agricultor para compararlas lado a lado:
    - Financiero (CU-FIN-004): ganancia neta, costo por quintal, margen.
    - Estimación: producción estimada total.
    - Producción real cosechada.

Además incluye la validación global del modelo (CU-EST-006) sobre todo
el histórico — la métrica que sustenta la tesis.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.application.use_cases.financiero.calcular_rentabilidad import CalcularRentabilidadUseCase
from app.application.use_cases.estimacion.comparar_estimacion_real import CompararEstimacionRealUseCase
from app.domain.repositories.i_estimacion_repository import IEstimacionRepository
from app.domain.repositories.i_compra_repository import ICompraRepository
from app.domain.repositories.i_resultado_financiero_repository import IResultadoFinancieroRepository
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class DashboardComparativoUseCase:
    """
    Implementa CU-REP-005 por composición de casos de uso existentes.
    """

    def __init__(
        self,
        db: Session,
        estimacion_repo: IEstimacionRepository,
        compra_repo: ICompraRepository,
        resultado_repo: IResultadoFinancieroRepository,
        temporada_parcela_repo: ITemporadaParcelaRepository,
    ):
        self.db = db
        self.estimacion_repo = estimacion_repo
        self.compra_repo = compra_repo
        self.resultado_repo = resultado_repo
        self.temporada_parcela_repo = temporada_parcela_repo

    @log_caso_de_uso("CU-REP-005 Dashboard Comparativo entre Temporadas")
    def ejecutar(self, agricultor_id: str) -> tuple:
        temporadas = self._listar_temporadas(agricultor_id)

        rentabilidad_uc = CalcularRentabilidadUseCase(
            db=self.db,
            compra_repo=self.compra_repo,
            resultado_repo=self.resultado_repo,
        )

        filas = []
        for t in temporadas:
            rentabilidad, status = rentabilidad_uc.ejecutar(
                temporada_id=t['id'],
                agricultor_id=agricultor_id,
            )
            if status != 200:
                continue

            estimaciones = self.estimacion_repo.listar_por_temporada(t['id'])
            produccion_estimada_qq = round(
                sum(e.valor_total_qq for e in estimaciones if e.valor_total_qq), 2
            )

            filas.append({
                'temporada_id': t['id'],
                'nombre': t['nombre'],
                'estado': t['estado'],
                'fecha_inicio': t['fecha_inicio'],
                'produccion_estimada_qq': produccion_estimada_qq,
                'produccion_real_qq': rentabilidad['ingresos'].get('produccion_qq'),
                'ganancia_neta': rentabilidad['resultado']['ganancia_neta'],
                'margen_rentabilidad_porcentaje':
                    rentabilidad['resultado']['margen_rentabilidad_porcentaje'],
                'costo_por_quintal': rentabilidad['resultado']['costo_por_quintal'],
                'hay_perdida': rentabilidad['resultado']['hay_perdida'],
            })

        # Validación global del modelo sobre todo el histórico.
        validacion_uc = CompararEstimacionRealUseCase(
            db=self.db,
            estimacion_repo=self.estimacion_repo,
            temporada_parcela_repo=self.temporada_parcela_repo,
        )
        validacion_global, _ = validacion_uc.ejecutar(agricultor_id=agricultor_id)

        # Agregados simples sobre las temporadas con resultado financiero.
        ganancias = [f['ganancia_neta'] for f in filas if f['ganancia_neta'] is not None]
        mejor = max(
            (f for f in filas if f['ganancia_neta'] is not None),
            key=lambda f: f['ganancia_neta'],
            default=None,
        )

        return {
            'total_temporadas': len(filas),
            'ganancia_acumulada': round(sum(ganancias), 2) if ganancias else 0.0,
            'mejor_temporada': (
                {'nombre': mejor['nombre'], 'ganancia_neta': mejor['ganancia_neta']}
                if mejor else None
            ),
            'validacion_global': validacion_global,
            'temporadas': filas,
        }, 200

    def _listar_temporadas(self, agricultor_id: str) -> list:
        """
        Lista las temporadas del agricultor (lectura simple, sin lógica
        de negocio) ordenadas de la más reciente a la más antigua.
        """
        rows = self.db.execute(
            text("""
                SELECT t.id, t.nombre, t.estado, t.fecha_inicio
                FROM temporadas t
                JOIN agricultores a ON t.agricultor_id = a.id
                WHERE a.usuario_id = CAST(:agricultor_id AS uuid)
                ORDER BY t.fecha_inicio DESC NULLS LAST
            """),
            {'agricultor_id': agricultor_id},
        ).fetchall()

        return [
            {
                'id': str(r.id),
                'nombre': r.nombre,
                'estado': r.estado,
                'fecha_inicio': str(r.fecha_inicio) if r.fecha_inicio else None,
            }
            for r in rows
        ]
