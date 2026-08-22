from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.parcela import Parcela


class IParcelaRepository(ABC):

    @abstractmethod
    def guardar(self, parcela: Parcela) -> Parcela:
        pass

    @abstractmethod
    def buscar_por_id(self, parcela_id: str) -> Optional[Parcela]:
        pass

    @abstractmethod
    def listar_por_lote(self, lote_id: str) -> List[Parcela]:
        pass

    @abstractmethod
    def actualizar(self, parcela: Parcela) -> Parcela:
        pass

    @abstractmethod
    def calcular_superficie_ha(self, geometria_wkt: str) -> float:
        pass