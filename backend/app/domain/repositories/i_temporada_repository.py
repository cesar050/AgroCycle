from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.temporada import Temporada


class ITemporadaRepository(ABC):

    @abstractmethod
    def guardar(self, temporada: Temporada) -> Temporada:
        pass

    @abstractmethod
    def buscar_por_id(self, temporada_id: str) -> Optional[Temporada]:
        pass

    @abstractmethod
    def listar_por_agricultor(self, agricultor_id: str) -> List[Temporada]:
        pass

    @abstractmethod
    def listar_activas_por_agricultor(self, agricultor_id: str) -> List[Temporada]:
        pass

    @abstractmethod
    def actualizar(self, temporada: Temporada) -> Temporada:
        pass