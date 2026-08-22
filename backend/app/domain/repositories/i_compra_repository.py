from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.compra import Compra


class ICompraRepository(ABC):

    @abstractmethod
    def guardar(self, compra: Compra) -> Compra:
        """Persiste una nueva compra en la base de datos."""
        pass

    @abstractmethod
    def obtener_por_id(self, compra_id: str) -> Optional[Compra]:
        """Busca una compra por su UUID."""
        pass

    @abstractmethod
    def listar_por_temporada(self, temporada_id: str) -> List[Compra]:
        """
        Retorna todas las compras de una temporada ordenadas por fecha.
        Es la base para calcular el total de gastos acumulados.
        """
        pass

    @abstractmethod
    def listar_por_categoria(
        self, temporada_id: str, categoria: str
    ) -> List[Compra]:
        """
        Retorna compras filtradas por categoría.
        Útil para ver cuánto se gastó solo en fertilizantes, por ejemplo.
        """
        pass

    @abstractmethod
    def total_por_categoria(self, temporada_id: str) -> dict:
        """
        Retorna el total gastado por cada categoría en una temporada.
        Hace el cálculo en la BD con GROUP BY — más eficiente que
        traer todos los registros y sumar en Python.

        Returns:
            dict con estructura:
            {
                'semillas': 250.00,
                'fertilizantes': 480.00,
                'agroquimicos': 120.00,
                'mano_obra': 200.00,
                'otros': 50.00,
                'total': 1100.00
            }
        """
        pass

    @abstractmethod
    def eliminar(self, compra_id: str) -> bool:
        """
        Elimina una compra. Retorna True si se eliminó correctamente.
        Solo se puede eliminar si la temporada está activa.
        """
        pass