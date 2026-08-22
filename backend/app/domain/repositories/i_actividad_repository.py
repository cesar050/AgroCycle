from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.actividad import Actividad


class IActividadRepository(ABC):

    @abstractmethod
    def guardar(self, actividad: Actividad) -> Actividad:
        pass

    @abstractmethod
    def buscar_por_id(self, actividad_id: str) -> Optional[Actividad]:
        pass

    @abstractmethod
    def listar_por_temporada(self, temporada_id: str) -> List[Actividad]:
        pass

    @abstractmethod
    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[Actividad]:
        pass