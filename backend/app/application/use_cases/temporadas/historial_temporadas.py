"""
CU-TEM-006 — Historial de temporadas del agricultor.

Retorna todas las temporadas cerradas con un resumen
de producción, financiero y comparativo entre temporadas.
Sirve para que el agricultor vea la evolución de su finca
año tras año y tome decisiones basadas en datos históricos.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.logging.logger import log_caso_de_uso


class HistorialTemporadasUseCase:
    """
    Implementa CU-TEM-006.

    Responsabilidades:
    1. Listar todas las temporadas del agricultor
    2. Por cada temporada incluir resumen de producción
       y financiero si están disponibles
    3. Calcular comparativos entre temporadas
    """

    def __init__(self, db: Session):
        self.db = db

    @log_caso_de_uso('CU-TEM-006 Historial de Temporadas')
    def ejecutar(self, agricultor_id: str) -> tuple:
        """
        Retorna el historial completo de temporadas del agricultor.

        Args:
            agricultor_id: UUID del usuario autenticado

        Returns:
            tuple (dict con historial, int código HTTP)
        """
        # 1. Obtener todas las temporadas con resumen
        temporadas = self._obtener_temporadas(agricultor_id)

        if not temporadas:
            return {
                'total': 0,
                'temporadas': [],
                'mensaje': 'No hay temporadas registradas aún.',
            }, 200

        # 2. Calcular comparativos
        comparativo = self._calcular_comparativo(temporadas)

        return {
            'total': len(temporadas),
            'temporadas': temporadas,
            'comparativo': comparativo,
        }, 200

    def _obtener_temporadas(self, agricultor_id: str) -> list:
        """
        Obtiene todas las temporadas con resumen de producción
        y financiero en una sola query eficiente.
        """
        rows = self.db.execute(
            text("""
                SELECT
                    t.id,
                    t.nombre,
                    t.estado,
                    t.fecha_inicio,
                    t.fecha_fin_estimada,
                    t.fecha_fin_real,
                    t.observaciones,
                    f.nombre                            AS finca_nombre,
                    c.nombre                            AS cultivo_nombre,
                    COUNT(tp.id)                        AS total_parcelas,
                    SUM(p.superficie_ha)                AS superficie_total_ha,
                    SUM(tp.produccion_real_qq)          AS produccion_total_qq,
                    SUM(tp.ingresos_totales)            AS ingresos_totales,
                    AVG(tp.precio_venta_qq)             AS precio_promedio_qq,
                    SUM(tp.volumen_vendido_qq)          AS volumen_vendido_qq,
                    SUM(tp.produccion_autoconsumo_qq)   AS autoconsumo_qq,
                    rf.costos_totales,
                    rf.ganancia_neta,
                    rf.margen_rentabilidad_porcentaje,
                    rf.costo_por_quintal
                FROM temporadas t
                JOIN agricultores a  ON t.agricultor_id = a.id
                JOIN fincas f        ON t.finca_id = f.id
                JOIN cultivos c      ON t.cultivo_id = c.id
                LEFT JOIN temporada_parcelas tp ON tp.temporada_id = t.id
                LEFT JOIN parcelas p            ON tp.parcela_id = p.id
                LEFT JOIN resultados_financieros rf ON rf.temporada_id = t.id
                WHERE a.usuario_id = CAST(:agricultor_id AS uuid)
                GROUP BY
                    t.id, t.nombre, t.estado, t.fecha_inicio,
                    t.fecha_fin_estimada, t.fecha_fin_real,
                    t.observaciones, f.nombre, c.nombre,
                    rf.costos_totales, rf.ganancia_neta,
                    rf.margen_rentabilidad_porcentaje,
                    rf.costo_por_quintal
                ORDER BY t.fecha_inicio DESC
            """),
            {'agricultor_id': agricultor_id}
        ).fetchall()

        return [self._fila_a_dict(r) for r in rows]

    def _fila_a_dict(self, r) -> dict:
        """Convierte una fila de resultado a dict estructurado."""
        produccion_qq = float(r.produccion_total_qq) if r.produccion_total_qq else None
        superficie_ha = float(r.superficie_total_ha) if r.superficie_total_ha else None

        return {
            'id': str(r.id),
            'nombre': r.nombre,
            'estado': r.estado,
            'finca': r.finca_nombre,
            'cultivo': r.cultivo_nombre,
            'fechas': {
                'inicio': str(r.fecha_inicio),
                'fin_estimado': str(r.fecha_fin_estimada) if r.fecha_fin_estimada else None,
                'fin_real': str(r.fecha_fin_real) if r.fecha_fin_real else None,
            },
            'produccion': {
                'total_parcelas': int(r.total_parcelas or 0),
                'superficie_total_ha': round(superficie_ha, 4) if superficie_ha else None,
                'produccion_total_qq': round(produccion_qq, 2) if produccion_qq else None,
                'rendimiento_qq_ha': round(
                    produccion_qq / superficie_ha, 2
                ) if produccion_qq and superficie_ha else None,
                'volumen_vendido_qq': float(r.volumen_vendido_qq) if r.volumen_vendido_qq else None,
                'autoconsumo_qq': float(r.autoconsumo_qq) if r.autoconsumo_qq else None,
                'precio_promedio_qq': round(
                    float(r.precio_promedio_qq), 2
                ) if r.precio_promedio_qq else None,
            },
            'financiero': {
                'ingresos_totales': float(r.ingresos_totales) if r.ingresos_totales else None,
                'costos_totales': float(r.costos_totales) if r.costos_totales else None,
                'ganancia_neta': float(r.ganancia_neta) if r.ganancia_neta else None,
                'margen_rentabilidad': float(
                    r.margen_rentabilidad_porcentaje
                ) if r.margen_rentabilidad_porcentaje else None,
                'costo_por_quintal': float(
                    r.costo_por_quintal
                ) if r.costo_por_quintal else None,
            },
            'observaciones': r.observaciones,
        }

    def _calcular_comparativo(self, temporadas: list) -> dict:
        """
        Calcula estadísticas comparativas entre todas las temporadas.
        Útil para que el agricultor vea tendencias año tras año.
        """
        producciones = [
            t['produccion']['produccion_total_qq']
            for t in temporadas
            if t['produccion']['produccion_total_qq']
        ]

        ganancias = [
            t['financiero']['ganancia_neta']
            for t in temporadas
            if t['financiero']['ganancia_neta'] is not None
        ]

        rendimientos = [
            t['produccion']['rendimiento_qq_ha']
            for t in temporadas
            if t['produccion']['rendimiento_qq_ha']
        ]

        return {
            'produccion': {
                'mejor_temporada_qq': max(producciones) if producciones else None,
                'peor_temporada_qq': min(producciones) if producciones else None,
                'promedio_qq': round(
                    sum(producciones) / len(producciones), 2
                ) if producciones else None,
                'mejor_rendimiento_qq_ha': max(rendimientos) if rendimientos else None,
            },
            'financiero': {
                'mejor_ganancia': max(ganancias) if ganancias else None,
                'peor_resultado': min(ganancias) if ganancias else None,
                'ganancia_promedio': round(
                    sum(ganancias) / len(ganancias), 2
                ) if ganancias else None,
                'temporadas_rentables': sum(
                    1 for g in ganancias if g > 0
                ),
                'temporadas_con_perdida': sum(
                    1 for g in ganancias if g < 0
                ),
            },
        }