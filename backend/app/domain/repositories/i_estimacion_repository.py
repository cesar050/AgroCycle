from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.estimacion import Estimacion


class IEstimacionRepository(ABC):

    @abstractmethod
    def guardar(self, estimacion: Estimacion) -> Estimacion:
        pass

    @abstractmethod
    def obtener_ultima_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> Optional[Estimacion]:
        """
        Retorna la estimación más reciente de una temporada_parcela.
        Es la que se muestra al agricultor en el dashboard.
        """
        pass

    @abstractmethod
    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[Estimacion]:
        """
        Retorna todas las estimaciones históricas de una parcela
        ordenadas de más antigua a más reciente.
        Sirve para graficar la evolución durante la temporada.
        """
        pass

    @abstractmethod
    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[Estimacion]:
        """
        Retorna la última estimación de cada parcela de la temporada.
        Sirve para el resumen consolidado del dashboard.
        """
        pass