"""
CU-FIN-007 — Comparar resultados financieros entre temporadas.

Reúne el resultado financiero consolidado de todas las temporadas
del agricultor (ingresos, costos, ganancia neta, margen y costo por
quintal) y los pone lado a lado para que pueda ver su evolución año
tras año: cuál fue la temporada más rentable, cuál dejó pérdida y si
la tendencia va mejorando o empeorando.

Reutiliza el repositorio de resultados financieros ya existente —
los resultados se calculan y persisten en CU-FIN-005
(CalcularRentabilidadUseCase), así que este caso de uso solo los
consolida y compara, sin recalcular nada.
"""
from sqlalchemy.orm import Session

from app.domain.repositories.i_resultado_financiero_repository import (
    IResultadoFinancieroRepository,
)
from app.infrastructure.logging.logger import log_caso_de_uso


class CompararFinanzasTemporadasUseCase:
    """
    Implementa CU-FIN-007.

    Responsabilidades:
    1. Obtener el resultado financiero de cada temporada del agricultor
    2. Ordenarlos cronológicamente para ver la evolución
    3. Calcular estadísticas comparativas (mejor, peor, promedio)
    4. Determinar la tendencia de la última temporada vs la anterior
    """

    def __init__(
        self,
        db: Session,
        resultado_repo: IResultadoFinancieroRepository,
    ):
        self.db = db
        self.resultado_repo = resultado_repo

    @log_caso_de_uso('CU-FIN-007 Comparar Finanzas entre Temporadas')
    def ejecutar(self, agricultor_id: str) -> tuple:
        """
        Retorna el comparativo financiero entre temporadas.

        Args:
            agricultor_id: UUID del usuario autenticado

        Returns:
            tuple (dict, int) con el comparativo y el código HTTP
        """
        filas = self.resultado_repo.listar_comparativo(agricultor_id)

        if not filas:
            return {
                'total_temporadas': 0,
                'temporadas': [],
                'comparativo': None,
                'mensaje': (
                    'Aún no hay resultados financieros para comparar. '
                    'Registra gastos y ventas y consulta la rentabilidad '
                    'de al menos una temporada.'
                ),
            }, 200

        temporadas = [self._fila_a_item(f) for f in filas]
        comparativo = self._calcular_comparativo(temporadas)

        return {
            'total_temporadas': len(temporadas),
            'temporadas': temporadas,
            'comparativo': comparativo,
        }, 200

    def _fila_a_item(self, f: dict) -> dict:
        """Normaliza una fila del repositorio a un item de comparación."""
        ganancia = f.get('ganancia_neta')
        return {
            'temporada_id': f['temporada_id'],
            'nombre': f['temporada_nombre'],
            'estado': f['estado'],
            'fecha_inicio': f['fecha_inicio'],
            'ingresos_totales': round(f.get('ingresos_totales') or 0, 2),
            'costos_totales': round(f.get('costos_totales') or 0, 2),
            'ganancia_neta': round(ganancia, 2) if ganancia is not None else None,
            'margen_rentabilidad_porcentaje': f.get('margen_rentabilidad_porcentaje'),
            'costo_por_quintal': f.get('costo_por_quintal'),
            'produccion_total_qq': f.get('produccion_total_qq'),
            'hay_perdida': ganancia is not None and ganancia < 0,
        }

    def _calcular_comparativo(self, temporadas: list) -> dict:
        """
        Calcula estadísticas comparativas y la tendencia reciente.
        Solo considera temporadas con ganancia neta calculada.
        """
        con_ganancia = [
            t for t in temporadas if t['ganancia_neta'] is not None
        ]
        ganancias = [t['ganancia_neta'] for t in con_ganancia]

        costos_qq = [
            t['costo_por_quintal']
            for t in temporadas
            if t['costo_por_quintal'] is not None
        ]

        mejor = max(
            con_ganancia, key=lambda t: t['ganancia_neta']
        ) if con_ganancia else None
        peor = min(
            con_ganancia, key=lambda t: t['ganancia_neta']
        ) if con_ganancia else None

        return {
            'mejor_temporada': {
                'nombre': mejor['nombre'],
                'ganancia_neta': mejor['ganancia_neta'],
            } if mejor else None,
            'peor_temporada': {
                'nombre': peor['nombre'],
                'ganancia_neta': peor['ganancia_neta'],
            } if peor else None,
            'ganancia_promedio': round(
                sum(ganancias) / len(ganancias), 2
            ) if ganancias else None,
            'temporadas_rentables': sum(1 for g in ganancias if g > 0),
            'temporadas_con_perdida': sum(1 for g in ganancias if g < 0),
            'mejor_costo_por_quintal': round(min(costos_qq), 2) if costos_qq else None,
            'tendencia': self._calcular_tendencia(con_ganancia),
        }

    def _calcular_tendencia(self, con_ganancia: list) -> dict:
        """
        Compara la última temporada con la anterior para indicar
        si el resultado mejora, empeora o se mantiene.
        Las temporadas vienen ordenadas cronológicamente (ASC).
        """
        if len(con_ganancia) < 2:
            return {
                'variacion': None,
                'direccion': 'sin_datos',
            }

        ultima = con_ganancia[-1]['ganancia_neta']
        anterior = con_ganancia[-2]['ganancia_neta']
        variacion = round(ultima - anterior, 2)

        if variacion > 0:
            direccion = 'mejora'
        elif variacion < 0:
            direccion = 'empeora'
        else:
            direccion = 'estable'

        return {
            'variacion': variacion,
            'direccion': direccion,
            'temporada_actual': con_ganancia[-1]['nombre'],
            'temporada_anterior': con_ganancia[-2]['nombre'],
        }
