from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.temporada_parcela import TemporadaParcela


class ITemporadaParcelaRepository(ABC):

    @abstractmethod
    def guardar(self, temporada_parcela: TemporadaParcela) -> TemporadaParcela:
        pass

    @abstractmethod
    def buscar_por_id(self, tp_id: str) -> Optional[TemporadaParcela]:
        pass

    @abstractmethod
    def listar_por_temporada(self, temporada_id: str) -> List[TemporadaParcela]:
        pass

    @abstractmethod
    def actualizar(self, temporada_parcela: TemporadaParcela) -> TemporadaParcela:
        pass

    @abstractmethod
    def existe_parcela_en_temporada(self, parcela_id: str, temporada_id: str) -> bool:
        pass