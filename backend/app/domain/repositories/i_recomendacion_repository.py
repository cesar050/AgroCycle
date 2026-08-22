from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.recomendacion_agronomica import RecomendacionAgronomica


class IRecomendacionRepository(ABC):

    @abstractmethod
    def guardar(
        self, recomendacion: RecomendacionAgronomica
    ) -> RecomendacionAgronomica:
        """Persiste una nueva recomendación agronómica."""
        pass

    @abstractmethod
    def obtener_por_id(
        self, recomendacion_id: str
    ) -> Optional[RecomendacionAgronomica]:
        """Busca una recomendación por su UUID."""
        pass

    @abstractmethod
    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[RecomendacionAgronomica]:
        """
        Retorna todas las recomendaciones de una temporada.
        Ordenadas por urgencia primero, luego por fecha descendente.
        Las urgentes aparecen siempre arriba.
        """
        pass

    @abstractmethod
    def listar_no_leidas_por_agricultor(
        self, agricultor_id: str
    ) -> List[RecomendacionAgronomica]:
        """
        Retorna recomendaciones pendientes de leer por el agricultor.
        Sirve para el badge de notificaciones en el dashboard.
        """
        pass

    @abstractmethod
    def marcar_leida(self, recomendacion_id: str) -> bool:
        """
        Marca una recomendación como leída por el agricultor.
        Retorna True si se actualizó correctamente.
        """
        pass