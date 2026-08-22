from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.observacion_tecnica import ObservacionTecnica


class IObservacionRepository(ABC):

    @abstractmethod
    def guardar(self, observacion: ObservacionTecnica) -> ObservacionTecnica:
        """Persiste una nueva observación técnica."""
        pass

    @abstractmethod
    def obtener_por_id(self, observacion_id: str) -> Optional[ObservacionTecnica]:
        """Busca una observación por su UUID."""
        pass

    @abstractmethod
    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[ObservacionTecnica]:
        """
        Retorna todas las observaciones de una temporada
        ordenadas de más reciente a más antigua.
        El agrónomo ve el historial completo de sus anotaciones.
        """
        pass

    @abstractmethod
    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[ObservacionTecnica]:
        """
        Retorna observaciones específicas de una parcela.
        Útil para ver el historial de una parcela en particular.
        """
        pass

    @abstractmethod
    def eliminar(self, observacion_id: str) -> bool:
        """
        Elimina una observación registrada por error.
        Retorna True si se eliminó correctamente.
        """
        pass