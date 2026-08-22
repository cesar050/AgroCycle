"""
Interfaz del repositorio del Usuario.
Define el contrato que debe cumplir cualquier implementacion de persistencia. 
La capa de dominio no sabe si los datos vienen de PostgreSQL, un archivo o una API.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.usuario import Usuario

class IUsuarioRepository(ABC):
    """
    Contrato abstracto para el repositorio de usuarios.
    Siguiendo el Dependency Inversion Principle de SOLID, 
    la logica de negocio depende de esta asbtraccion, no de PostgreSQL directamente.
    """
    @abstractmethod
    def guardar(self, usuario:Usuario)-> Usuario:
        """Persiste un nuevo usuario o actualiza uno existente."""
        pass
    
    @abstractmethod
    def buscar_por_id(self, usuario_id:str)-> Optional[Usuario]:
        """ Busca un usuario por su UUID. Retorna None si no existe."""
        pass
    
    @abstractmethod
    def buscar_por_correo(self, correo:str)->Optional[Usuario]:
        """Busca un usuario por correo electronico. Retorna None si no existe."""
        pass
    
    @abstractmethod
    def existe_correo(self, correo: str) -> bool:
        """ Verifica si un correo ya esta registrado en el sistema."""
        pass
    
    @abstractmethod
    def actualizar(self, usuario: Usuario)-> Usuario:
        """Actualiza los datos de un usuario existente."""
        pass

    @abstractmethod
    def listar_todos(self)-> list:
        """Retorna todos los usuarios registrados en el sistema."""
        pass

    @abstractmethod
    def buscar_por_id(self, usuario_id: str):
        """Busca usuario por UUID, Retorna None si no existe."""
    
    @abstractmethod
    def desactivar(self, usuario_id:str)-> bool:
        """Desactiva un usuario. Retorna True si lo encontro y desactivo."""
        pass
    
