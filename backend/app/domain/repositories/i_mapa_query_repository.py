from abc import ABC, abstractmethod
from typing import Optional, List


class IMapaQueryRepository(ABC):
    """
    Puerto de solo lectura para las vistas agregadas del modulo Mapa
    (finca+lotes+parcelas con geojson, centroides, bbox). Mantiene el SQL
    de estas consultas fuera de la capa interfaces/, detras de un contrato
    de dominio, igual que el resto de repositorios.
    """

    @abstractmethod
    def obtener_finca_con_geojson(self, finca_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def listar_lotes_con_geojson(self, finca_id: str) -> List[dict]:
        pass

    @abstractmethod
    def listar_parcelas_con_estado(self, finca_id: str) -> List[dict]:
        pass

    @abstractmethod
    def listar_parcelas_geojson_simple(self, finca_id: str) -> List[dict]:
        pass

    @abstractmethod
    def obtener_geometria_parcela(self, parcela_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def listar_centroides_parcelas(self, finca_id: str) -> List[dict]:
        pass

    @abstractmethod
    def obtener_bbox_parcelas(self, finca_id: str) -> Optional[tuple]:
        pass
