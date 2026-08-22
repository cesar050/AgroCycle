from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.lote import Lote


class ILoteRepository(ABC):

    @abstractmethod
    def guardar(self, lote: Lote) -> Lote:
        pass

    @abstractmethod
    def buscar_por_id(self, lote_id: str) -> Optional[Lote]:
        pass

    @abstractmethod
    def listar_por_finca(self, finca_id: str) -> List[Lote]:
        pass

    @abstractmethod
    def actualizar(self, lote: Lote) -> Lote:
        pass

    @abstractmethod
    def existe_nombre_en_finca(self, nombre: str, finca_id: str) -> bool:
        pass