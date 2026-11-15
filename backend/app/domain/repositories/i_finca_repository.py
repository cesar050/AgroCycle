from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.finca import Finca


class IFincaRepository(ABC):

    @abstractmethod
    def guardar(self, finca: Finca) -> Finca:
        pass

    @abstractmethod
    def buscar_por_id(self, finca_id: str) -> Optional[Finca]:
        pass

    @abstractmethod
    def listar_por_agricultor(self, agricultor_id: str) -> List[Finca]:
        pass

    @abstractmethod
    def actualizar(self, finca: Finca) -> Finca:
        pass

    @abstractmethod
    def existe_nombre_para_agricultor(self, nombre: str, agricultor_id: str) -> bool:
        pass

    @abstractmethod
    def calcular_superficie_ha(self, geometria_wkt: str) -> float:
        pass

    @abstractmethod
    def contiene_geometria(self, finca_id: str, geometria_wkt: str) -> bool:
        pass

    @abstractmethod
    def contar_lotes_activos(self, finca_id: str) -> int:
        pass