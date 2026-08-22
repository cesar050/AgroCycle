from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


KY_MAIZ = {
    'emergencia':             0.20,
    'crecimiento_vegetativo': 0.40,
    'floracion':              1.50,
    'llenado_grano':          0.50,
    'maduracion':             0.20,
    'pre_siembra':            0.00,
    'cosecha':                0.00,
    'post_cosecha':           0.00,
}


class FAO33Calculator:
    """
    Implementa el modelo FAO-33 (Stewart, 1977).
    Ya = Ym * (1 - Ky * (1 - Ks))

    Recibe la sesión de base de datos inyectada desde el caso de uso.
    No importa nada de infraestructura directamente.
    """

    def __init__(self, db: Session):
        self.db = db

    def calcular(
        self,
        temporada_parcela_id: str,
        produccion_potencial_qq_ha: float,
        ciclo_vegetativo_dias: int,
        superficie_ha: float,
        pendiente_porcentaje: Optional[float] = None,
    ) -> dict:

        datos_por_etapa = self._datos_por_etapa(temporada_parcela_id)

        if not datos_por_etapa:
            return self._estimacion_sin_datos(
                produccion_potencial_qq_ha, superficie_ha
            )

        reduccion_total, factores, detalle_etapas = self._calcular_reduccion(
            datos_por_etapa, produccion_potencial_qq_ha
        )

        factor_pendiente = self._factor_pendiente(pendiente_porcentaje)

        produccion_base = max(produccion_potencial_qq_ha - reduccion_total, 0.0)
        produccion_estimada_qq_ha = round(produccion_base * factor_pendiente, 2)
        produccion_total_qq = round(produccion_estimada_qq_ha * superficie_ha, 2)

        dias_con_datos = sum(e.get('dias_con_datos', 0) for e in datos_por_etapa)
        margen_error = self._margen_error(dias_con_datos, ciclo_vegetativo_dias)
        ks_global = self._ks_ponderado(datos_por_etapa)

        return {
            'valor_qq_ha': produccion_estimada_qq_ha,
            'valor_total_qq': produccion_total_qq,
            'margen_error_porcentaje': margen_error,
            'etapas_detalle': detalle_etapas,
            'factores_positivos': factores['positivos'],
            'factores_negativos': factores['negativos'],
            'variables_entrada': {
                'produccion_potencial_qq_ha': produccion_potencial_qq_ha,
                'ciclo_vegetativo_dias': ciclo_vegetativo_dias,
                'superficie_ha': superficie_ha,
                'pendiente_porcentaje': pendiente_porcentaje,
                'factor_pendiente': round(factor_pendiente, 4),
                'ks_global_ponderado': round(ks_global, 4),
                'dias_con_datos': dias_con_datos,
                'reduccion_total_qq_ha': round(reduccion_total, 2),
            }
        }

    def _datos_por_etapa(self, temporada_parcela_id: str) -> list:
        """
        Agrupa los indicadores de estrés por etapa fenológica histórica.
        Usa estado_fenologico guardado día a día — no el estado actual.
        """
        sql = text("""
            SELECT
                ies.estado_fenologico                   AS etapa,
                COUNT(*)                                AS dias_con_datos,
                AVG(ies.valor_ks)                       AS ks_promedio,
                SUM(dc.precipitacion_mm)                AS precip_total,
                AVG(dc.temperatura_promedio_c)          AS temp_promedio
            FROM indicadores_estres_hidrico ies
            JOIN temporada_parcelas tp
                ON ies.temporada_parcela_id = tp.id
            JOIN parcelas p
                ON tp.parcela_id = p.id
            JOIN datos_climaticos dc
                ON dc.parcela_id = p.id
                AND dc.fecha = ies.fecha
            WHERE ies.temporada_parcela_id = CAST(:tp_id AS uuid)
              AND ies.estado_fenologico IS NOT NULL
            GROUP BY ies.estado_fenologico
            ORDER BY MIN(ies.fecha)
        """)

        rows = self.db.execute(
            sql, {'tp_id': temporada_parcela_id}
        ).fetchall()

        return [
            {
                'etapa': r.etapa,
                'dias_con_datos': int(r.dias_con_datos or 0),
                'ks_promedio': float(r.ks_promedio or 1.0),
                'precip_total': float(r.precip_total or 0),
                'temp_promedio': float(r.temp_promedio or 20.0),
            }
            for r in rows
        ]
    
    def _calcular_reduccion(
        self, datos_por_etapa: list, produccion_potencial: float
    ) -> tuple:
        reduccion_total = 0.0
        factores_positivos = []
        factores_negativos = []
        detalle_etapas = []

        for d in datos_por_etapa:
            etapa = d['etapa']
            ky = KY_MAIZ.get(etapa, 0.0)
            ks = d['ks_promedio']
            reduccion_etapa = 0.0

            if ky > 0:
                deficit = max(1.0 - ks, 0.0)
                reduccion_etapa = produccion_potencial * ky * deficit
                reduccion_total += reduccion_etapa

            if ks >= 0.90:
                factores_positivos.append({
                    'etapa': etapa,
                    'descripcion': f'Humedad óptima en {etapa.replace("_", " ")} (Ks={ks:.2f}) — sin pérdida de rendimiento en esta etapa',
                    'beneficio_qq_ha': round(produccion_potencial * ky * 1.0, 2),
                })
            elif ks < 0.70:
                factores_negativos.append({
                    'etapa': etapa,
                    'descripcion': f'Estrés hídrico en {etapa.replace("_", " ")} (Ks={ks:.2f})',
                    'impacto_qq_ha': round(reduccion_etapa, 2),
                    'reduccion_porcentaje': round((1.0 - ks) * ky * 100, 1),
                })

            detalle_etapas.append({
                'etapa': etapa,
                'ky': ky,
                'ks_promedio': round(ks, 4),
                'reduccion_qq_ha': round(reduccion_etapa, 2),
                'dias_con_datos': d['dias_con_datos'],
                'precip_total_mm': round(d['precip_total'], 1),
                'temp_promedio_c': round(d['temp_promedio'], 1),
            })

        return reduccion_total, {
            'positivos': factores_positivos,
            'negativos': factores_negativos,
        }, detalle_etapas

    def _ks_ponderado(self, datos_por_etapa: list) -> float:
        numerador = 0.0
        denominador = 0.0
        for d in datos_por_etapa:
            ky = KY_MAIZ.get(d['etapa'], 0.0)
            if ky > 0:
                numerador += d['ks_promedio'] * ky
                denominador += ky
        return (numerador / denominador) if denominador > 0 else 1.0

    def _factor_pendiente(self, pendiente: Optional[float]) -> float:
        """
        Parcela Choza tiene 10.17% → factor 0.97.
        """
        if not pendiente:
            return 1.00
        if pendiente < 5:
            return 1.00
        elif pendiente < 15:
            return 0.97
        elif pendiente < 25:
            return 0.93
        else:
            return 0.88

    def _margen_error(
        self, dias_con_datos: int, ciclo_vegetativo_dias: int
    ) -> float:
        cobertura = min(dias_con_datos / max(ciclo_vegetativo_dias, 1), 1.0)
        margen = 35.0 - (cobertura * 27.0)
        return round(max(margen, 8.0), 1)

    def _estimacion_sin_datos(
        self, produccion_potencial: float, superficie_ha: float
    ) -> dict:
        return {
            'valor_qq_ha': round(produccion_potencial * 0.70, 2),
            'valor_total_qq': round(produccion_potencial * 0.70 * superficie_ha, 2),
            'margen_error_porcentaje': 35.0,
            'etapas_detalle': [],
            'factores_positivos': [],
            'factores_negativos': [{
                'etapa': 'general',
                'descripcion': 'Sin datos climáticos disponibles. Estimación basada en potencial de variedad con factor de seguridad del 30%.',
                'impacto_qq_ha': round(produccion_potencial * 0.30, 2),
            }],
            'variables_entrada': {
                'produccion_potencial_qq_ha': produccion_potencial,
                'superficie_ha': superficie_ha,
                'dias_con_datos': 0,
            }
        }