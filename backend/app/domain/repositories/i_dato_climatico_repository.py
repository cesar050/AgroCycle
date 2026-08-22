from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from app.domain.entities.dato_climatico import DatoClimatico


class IDatoClimaticoRepository(ABC):

    @abstractmethod
    def guardar(self, dato: DatoClimatico) -> DatoClimatico:
        pass

    @abstractmethod
    def guardar_lote(self, datos: List[DatoClimatico]) -> int:
        pass

    @abstractmethod
    def buscar_por_parcela_y_fecha(
        self, parcela_id: str, fecha: date
    ) -> Optional[DatoClimatico]:
        pass

    @abstractmethod
    def listar_por_parcela_y_rango(
        self, parcela_id: str, fecha_inicio: date, fecha_fin: date
    ) -> List[DatoClimatico]:
        pass

    @abstractmethod
    def actualizar_precipitacion(
        self, parcela_id: str, fecha: date, precipitacion_adicional: float
    ) -> bool:
        pass

    @abstractmethod
    def fechas_existentes(
        self, parcela_id: str, fecha_inicio: date, fecha_fin: date
    ) -> set:
        pass