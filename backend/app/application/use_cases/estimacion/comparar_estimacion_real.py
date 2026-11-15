"""
CU-EST-006 — Comparar Estimación vs Producción Real.

Caso de uso de VALIDACIÓN CIENTÍFICA del motor predictivo.
Reúne todas las parcelas del agricultor que ya fueron cosechadas
(con `produccion_real_qq` registrada) y que tienen al menos una
estimación FAO-33/FAO-56 generada, y calcula dos métricas de
precisión estándar en la literatura agronómica:

    - MAPE (Mean Absolute Percentage Error): error medio
      absoluto porcentual entre lo estimado y lo realmente cosechado.
    - R²   (Coeficiente de Determinación): proporción de la
      varianza de la cosecha real explicada por el modelo.

RIGOR: si existen menos de 2 pares válidos (real + estimación),
NO se inventa ninguna métrica — se devuelve `suficiente=False` con
un mensaje explícito. Estos números sustentan la defensa de tesis;
la honestidad del dato pesa más que llenar un gráfico.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.domain.repositories.i_estimacion_repository import IEstimacionRepository
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


# Umbral agronómico: por encima de este MAPE la estimación se
# considera poco confiable para decisiones de manejo / comercialización.
UMBRAL_MAPE_ALERTA = 20.0
UMBRAL_MAPE_ADVERTENCIA = 10.0
MIN_PARES_VALIDOS = 2


class CompararEstimacionRealUseCase:
    """
    Implementa CU-EST-006.

    Responsabilidades:
    1. Reunir los pares (estimado, real) del agricultor.
    2. Calcular error absoluto y porcentual por parcela.
    3. Calcular MAPE, R² (y RMSE como apoyo) sobre el conjunto.
    4. Emitir una alerta agronómica según el nivel de error.
    5. Negarse a reportar métricas con menos de 2 pares.
    """

    def __init__(
        self,
        db: Session,
        estimacion_repo: IEstimacionRepository,
        temporada_parcela_repo: ITemporadaParcelaRepository,
    ):
        self.db = db
        self.estimacion_repo = estimacion_repo
        self.temporada_parcela_repo = temporada_parcela_repo

    @log_caso_de_uso("CU-EST-006 Comparar Estimación vs Producción Real")
    def ejecutar(
        self,
        agricultor_id: str,
        temporada_id: Optional[str] = None,
    ) -> tuple:
        """
        Args:
            agricultor_id: UUID del usuario (verifica pertenencia).
            temporada_id: UUID opcional para restringir a una temporada.

        Returns:
            tuple (dict, int) con el resultado y el código HTTP.
        """
        puntos = self._reunir_pares(agricultor_id, temporada_id)
        n = len(puntos)

        # RIGOR CIENTÍFICO: sin 2 pares no hay métrica honesta posible.
        if n < MIN_PARES_VALIDOS:
            return {
                'suficiente': False,
                'n_pares': n,
                'min_requerido': MIN_PARES_VALIDOS,
                'mensaje': (
                    'Se requieren al menos 2 parcelas cosechadas con '
                    'estimación registrada para calcular R². '
                    f'Actualmente hay {n} par(es) válido(s).'
                ),
                'puntos': puntos,
            }, 200

        reales = [p['real_qq'] for p in puntos]
        estimados = [p['estimado_qq'] for p in puntos]

        # MAPE = promedio de los errores porcentuales individuales.
        mape = sum(p['error_pct'] for p in puntos) / n

        # R² = 1 - SS_res / SS_tot
        #   SS_res = Σ (real - estimado)²
        #   SS_tot = Σ (real - promedio(real))²
        promedio_real = sum(reales) / n
        ss_res = sum((r - e) ** 2 for r, e in zip(reales, estimados))
        ss_tot = sum((r - promedio_real) ** 2 for r in reales)

        if ss_tot == 0:
            # Todas las cosechas reales son idénticas: la varianza es 0 y
            # R² queda matemáticamente indefinido. No se fabrica un valor.
            r2 = None
            nota_r2 = (
                'R² indefinido: todas las parcelas tienen la misma '
                'producción real (varianza nula).'
            )
        else:
            r2 = round(1 - (ss_res / ss_tot), 4)
            nota_r2 = None

        # RMSE (Raíz del Error Cuadrático Medio) — métrica de apoyo en qq.
        rmse = round((ss_res / n) ** 0.5, 2)

        algoritmos = [p['algoritmo'] for p in puntos if p['algoritmo']]
        algoritmo_predominante = (
            max(set(algoritmos), key=algoritmos.count) if algoritmos else None
        )

        return {
            'suficiente': True,
            'n_pares': n,
            'metricas': {
                'mape': round(mape, 2),
                'r2': r2,
                'rmse': rmse,
                'nota_r2': nota_r2,
            },
            'alerta': self._construir_alerta(mape),
            'algoritmo_predominante': algoritmo_predominante,
            'puntos': puntos,
        }, 200

    def _construir_alerta(self, mape: float) -> dict:
        """
        Semáforo agronómico sobre el MAPE global.
        """
        if mape > UMBRAL_MAPE_ALERTA:
            nivel, color = 'alta', 'rojo'
            mensaje = (
                f'El error medio ({mape:.1f}%) supera el umbral del '
                f'{UMBRAL_MAPE_ALERTA:.0f}%. Las estimaciones deben tomarse '
                'con cautela para decisiones de comercialización.'
            )
        elif mape > UMBRAL_MAPE_ADVERTENCIA:
            nivel, color = 'media', 'naranja'
            mensaje = (
                f'El error medio ({mape:.1f}%) es moderado. El modelo es '
                'orientativo pero conviene seguir recopilando cosechas.'
            )
        else:
            nivel, color = 'baja', 'verde'
            mensaje = (
                f'El error medio ({mape:.1f}%) está dentro de un rango '
                'confiable para la toma de decisiones.'
            )

        return {
            'nivel': nivel,
            'color': color,
            'umbral_mape': UMBRAL_MAPE_ALERTA,
            'mensaje': mensaje,
        }

    def _reunir_pares(
        self,
        agricultor_id: str,
        temporada_id: Optional[str],
    ) -> list:
        """
        Obtiene, por cada parcela cosechada del agricultor, la última
        estimación generada en/antes de la cosecha (campo valor_total_qq).
        Usa un LATERAL JOIN para quedarse con una sola estimación por
        parcela sin traer el histórico completo.
        """
        sql = text("""
            SELECT
                tp.id                       AS tp_id,
                tp.produccion_real_qq       AS real_qq,
                tp.fecha_cosecha,
                p.nombre                    AS parcela_nombre,
                t.id                        AS temporada_id,
                t.nombre                    AS temporada_nombre,
                est.valor_total_qq          AS estimado_qq,
                est.algoritmo_usado,
                est.fecha_generacion
            FROM temporada_parcelas tp
            JOIN parcelas p
                ON tp.parcela_id = p.id
            JOIN temporadas t
                ON tp.temporada_id = t.id
            JOIN agricultores a
                ON t.agricultor_id = a.id
            JOIN LATERAL (
                SELECT ep.valor_total_qq, ep.algoritmo_usado, ep.fecha_generacion
                FROM estimaciones_produccion ep
                WHERE ep.temporada_parcela_id = tp.id
                  AND ep.valor_total_qq IS NOT NULL
                  AND (
                        tp.fecha_cosecha IS NULL
                        OR ep.fecha_generacion::date <= tp.fecha_cosecha
                      )
                ORDER BY ep.fecha_generacion DESC
                LIMIT 1
            ) est ON TRUE
            WHERE a.usuario_id = CAST(:agricultor_id AS uuid)
              AND tp.produccion_real_qq IS NOT NULL
              AND tp.produccion_real_qq > 0
              AND tp.activo = true
              AND (
                    CAST(:temporada_id AS uuid) IS NULL
                    OR t.id = CAST(:temporada_id AS uuid)
                  )
            ORDER BY t.fecha_inicio DESC NULLS LAST, p.nombre
        """)

        rows = self.db.execute(sql, {
            'agricultor_id': agricultor_id,
            'temporada_id': temporada_id,
        }).fetchall()

        puntos = []
        for r in rows:
            real = float(r.real_qq)
            estimado = float(r.estimado_qq)
            error_abs = abs(real - estimado)
            error_pct = (error_abs / real) * 100  # real > 0 garantizado por el WHERE

            puntos.append({
                'temporada_parcela_id': str(r.tp_id),
                'parcela_nombre': r.parcela_nombre,
                'temporada_id': str(r.temporada_id),
                'temporada_nombre': r.temporada_nombre,
                'real_qq': round(real, 2),
                'estimado_qq': round(estimado, 2),
                'error_abs': round(error_abs, 2),
                'error_pct': round(error_pct, 2),
                'algoritmo': r.algoritmo_usado,
                'fecha_cosecha': str(r.fecha_cosecha) if r.fecha_cosecha else None,
                'fecha_estimacion': (
                    r.fecha_generacion.isoformat() if r.fecha_generacion else None
                ),
            })

        return puntos
