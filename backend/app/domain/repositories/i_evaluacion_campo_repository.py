from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.evaluacion_campo import EvaluacionCampo


class IEvaluacionCampoRepository(ABC):

    @abstractmethod
    def guardar(self, evaluacion: EvaluacionCampo) -> EvaluacionCampo:
        """Persiste una nueva evaluación de campo."""
        pass

    @abstractmethod
    def obtener_por_id(
        self, evaluacion_id: str
    ) -> Optional[EvaluacionCampo]:
        """Busca una evaluación por su UUID."""
        pass

    @abstractmethod
    def listar_por_temporada(
        self, temporada_id: str
    ) -> List[EvaluacionCampo]:
        """
        Retorna todas las evaluaciones de campo de una temporada
        ordenadas cronológicamente de más antigua a más reciente.
        Permite ver la evolución del cultivo durante la temporada.
        """
        pass

    @abstractmethod
    def listar_por_temporada_parcela(
        self, temporada_parcela_id: str
    ) -> List[EvaluacionCampo]:
        """
        Retorna evaluaciones específicas de una parcela.
        Útil para ver cómo evolucionó esa parcela en particular.
        """
        pass