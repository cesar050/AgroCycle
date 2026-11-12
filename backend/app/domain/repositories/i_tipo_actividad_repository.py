"""
Interfaz del repositorio de catalogo de Tipos de Actividad.
Pertenece a la capa de dominio: define el contrato que la
infraestructura debe implementar, sin conocer PostgreSQL.
"""
from abc import ABC, abstractmethod
from typing import List


class ITipoActividadRepository(ABC):

    @abstractmethod
    def listar_activos(self) -> List[dict]:
        """Retorna los tipos de actividad activos del catalogo."""
        raise NotImplementedError
