from abc import ABC, abstractmethod
from typing import List


class ITipoSueloRepository(ABC):

    @abstractmethod
    def listar_activos(self) -> List[dict]:
        pass
