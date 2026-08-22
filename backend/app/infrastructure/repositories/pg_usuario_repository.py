"""
Implementación PostgreSQL del repositorio de Usuario.
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.domain.entities.usuario import Usuario
from app.domain.repositories.i_usuario_repository import IUsuarioRepository
from app.infrastructure.models.usuario_model import UsuarioModel
import uuid


class PgUsuarioRepository(IUsuarioRepository):

    def __init__(self, db: Session):
        self.db = db

    def guardar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel(
            id=uuid.UUID(usuario.id),
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            correo=usuario.correo,
            password_hash=usuario.password_hash,
            rol_id=usuario.rol_id,
            activo=usuario.activo,
            correo_verificado=usuario.correo_verificado,
            token_verificacion=usuario.token_verificacion
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def buscar_por_id(self, usuario_id: str) -> Optional[Usuario]:
        modelo = self.db.query(UsuarioModel).filter(
            UsuarioModel.id == uuid.UUID(usuario_id)
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def buscar_por_correo(self, correo: str) -> Optional[Usuario]:
        modelo = self.db.query(UsuarioModel).filter(
            UsuarioModel.correo == correo.lower().strip()
        ).first()
        return self._modelo_a_entidad(modelo) if modelo else None

    def existe_correo(self, correo: str) -> bool:
        return self.db.query(UsuarioModel).filter(
            UsuarioModel.correo == correo.lower().strip()
        ).count() > 0

    def actualizar(self, usuario: Usuario) -> Usuario:
        modelo = self.db.query(UsuarioModel).filter(
            UsuarioModel.id == uuid.UUID(usuario.id)
        ).first()
        if not modelo:
            raise ValueError(f"Usuario {usuario.id} no encontrado")

        modelo.nombre = usuario.nombre
        modelo.apellido = usuario.apellido
        modelo.activo = usuario.activo
        modelo.correo_verificado = usuario.correo_verificado
        modelo.token_verificacion = usuario.token_verificacion
        modelo.intentos_fallidos = usuario.intentos_fallidos
        modelo.bloqueado_hasta = usuario.bloqueado_hasta
        modelo.ultimo_acceso = usuario.ultimo_acceso
        modelo.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(modelo)
        return self._modelo_a_entidad(modelo)

    def listar_todos(self)-> list:
        """
        Retorna todos los usuarios ordenados por fecha de creacion.
        El mas reciente aparece primero.
        """
        modelos = self.db.query(UsuarioModel).order_by(
            UsuarioModel.created_at.desc()
        ).all()
        return [self._modelo_a_entidad(m) for m in modelos]
    
    def desactivar(self, usuario_id: str) -> bool:
        """
        Desactiva un usuario por su UUID. 
        No lo elimina, solo cambia de activo a false.
        Esto preserva el historial - principio de o borrar datos en sistemas productivos
        """
        modelo = self.db.query(UsuarioModel).filter(
            UsuarioModel.id == uuid.UUID(usuario_id)
        ).first()
        if not modelo:
            return False
        modelo.activo = False
        self.db.commit()
        return True

    def _modelo_a_entidad(self, modelo: UsuarioModel) -> Usuario:
        return Usuario(
            id=str(modelo.id),
            nombre=modelo.nombre,
            apellido=modelo.apellido,
            correo=modelo.correo,
            password_hash=modelo.password_hash,
            rol_id=modelo.rol_id,
            activo=modelo.activo,
            correo_verificado=modelo.correo_verificado,
            token_verificacion=modelo.token_verificacion,
            ultimo_acceso=modelo.ultimo_acceso,
            intentos_fallidos=modelo.intentos_fallidos,
            bloqueado_hasta=modelo.bloqueado_hasta,
            created_at=modelo.created_at,
            updated_at=modelo.updated_at
        )
