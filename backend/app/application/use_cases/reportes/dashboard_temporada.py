"""
CU-REP-004 — Consultar Dashboard General de Temporada.

NO duplica lógica de negocio: COMPONE en un solo JSON los datos que
ya producen otros módulos para una temporada concreta —
    - Financiero (CU-FIN-004): rentabilidad, costo por quintal, ganancia.
    - Estimación (listar_por_temporada): producción total estimada.
    - Validación (CU-EST-006): MAPE / R² de esa temporada.

El dashboard climático NO se recalcula aquí; el frontend consume sus
endpoints existentes por HTTP si lo necesita.
"""
from sqlalchemy.orm import Session

from app.application.use_cases.financiero.calcular_rentabilidad import CalcularRentabilidadUseCase
from app.application.use_cases.estimacion.comparar_estimacion_real import CompararEstimacionRealUseCase
from app.domain.repositories.i_estimacion_repository import IEstimacionRepository
from app.domain.repositories.i_compra_repository import ICompraRepository
from app.domain.repositories.i_resultado_financiero_repository import IResultadoFinancieroRepository
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class DashboardTemporadaUseCase:
    """
    Implementa CU-REP-004 por composición de casos de uso existentes.
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

    @log_caso_de_uso("CU-REP-004 Dashboard General de Temporada")
    def ejecutar(self, temporada_id: str, agricultor_id: str) -> tuple:
        # 1. Financiero (CU-FIN-004) — también verifica pertenencia.
        rentabilidad_uc = CalcularRentabilidadUseCase(
            db=self.db,
            compra_repo=self.compra_repo,
            resultado_repo=self.resultado_repo,
        )
        rentabilidad, status = rentabilidad_uc.ejecutar(
            temporada_id=temporada_id,
            agricultor_id=agricultor_id,
        )
        if status != 200:
            # Error o temporada inexistente: se propaga tal cual.
            return rentabilidad, status

        # 2. Estimación consolidada (producción total estimada de la temporada).
        estimaciones = self.estimacion_repo.listar_por_temporada(temporada_id)
        produccion_estimada_qq = round(
            sum(e.valor_total_qq for e in estimaciones if e.valor_total_qq), 2
        )

        # 3. Validación científica de esta temporada (CU-EST-006).
        validacion_uc = CompararEstimacionRealUseCase(
            db=self.db,
            estimacion_repo=self.estimacion_repo,
            temporada_parcela_repo=self.temporada_parcela_repo,
        )
        validacion, _ = validacion_uc.ejecutar(
            agricultor_id=agricultor_id,
            temporada_id=temporada_id,
        )

        produccion_real_qq = rentabilidad['ingresos'].get('produccion_qq')

        # Desviación global estimado vs real (si ya hay cosecha).
        desviacion_pct = None
        if produccion_real_qq and produccion_estimada_qq:
            desviacion_pct = round(
                (produccion_estimada_qq - produccion_real_qq)
                / produccion_real_qq * 100,
                2,
            )

        return {
            'temporada': rentabilidad['temporada'],
            'produccion': {
                'estimada_qq': produccion_estimada_qq,
                'real_qq': produccion_real_qq,
                'parcelas_estimadas': len(estimaciones),
                'desviacion_pct': desviacion_pct,
            },
            'financiero': {
                'gastos_total': rentabilidad['gastos']['total'],
                'ingresos_total': rentabilidad['ingresos']['total'],
                'ganancia_neta': rentabilidad['resultado']['ganancia_neta'],
                'margen_rentabilidad_porcentaje':
                    rentabilidad['resultado']['margen_rentabilidad_porcentaje'],
                'costo_por_quintal': rentabilidad['resultado']['costo_por_quintal'],
                'hay_perdida': rentabilidad['resultado']['hay_perdida'],
                'interpretacion': rentabilidad['resultado']['interpretacion'],
            },
            'validacion': validacion,
        }, 200
