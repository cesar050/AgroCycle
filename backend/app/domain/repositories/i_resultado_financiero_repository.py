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