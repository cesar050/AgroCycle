from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.resultado_financiero import ResultadoFinanciero


class IResultadoFinancieroRepository(ABC):

    @abstractmethod
    def guardar(
        self, resultado: ResultadoFinanciero
    ) -> ResultadoFinanciero:
        """Crea o actualiza el resultado financiero de una temporada."""
        pass

    @abstractmethod
    def obtener_por_temporada(
        self, temporada_id: str
    ) -> Optional[ResultadoFinanciero]:
        """
        Retorna el resultado financiero de una temporada.
        Retorna None si aún no se ha calculado.
        """
        pass

    @abstractmethod
    def listar_por_agricultor(
        self, agricultor_id: str
    ) -> List[ResultadoFinanciero]:
        """
        Retorna resultados financieros de todas las temporadas
        del agricultor ordenadas de más reciente a más antigua.
        Sirve para el comparativo entre temporadas.
        """
        pass

    @abstractmethod
    def listar_comparativo(
        self, agricultor_id: str
    ) -> List[dict]:
        """
        Retorna el resultado financiero de cada temporada del
        agricultor enriquecido con el nombre y estado de la
        temporada, ordenado cronológicamente (más antigua primero)
        para analizar la evolución entre temporadas.

        Soporta CU-FIN-007 — Comparar Resultados Financieros
        entre Temporadas. Devuelve diccionarios planos porque el
        nombre de la temporada no forma parte de la entidad de
        dominio ResultadoFinanciero.

        Cada elemento tiene la forma:
            {
                'temporada_id': str,
                'temporada_nombre': str,
                'estado': str,
                'fecha_inicio': str (ISO),
                'ingresos_totales': float,
                'costos_totales': float,
                'ganancia_neta': float | None,
                'margen_rentabilidad_porcentaje': float | None,
                'costo_por_quintal': float | None,
                'produccion_total_qq': float | None,
            }
        """
        pass