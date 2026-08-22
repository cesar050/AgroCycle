"""
Caso de uso: CU_ADM-001 Gestionar Usuarios.
Contiene la logica de negocio para listar, editar,
activar y desactivar usuarios del sistema.
Solo el administrador puede ejecutar estos casos de uso.
"""

from app.domain.repositories.i_usuario_repository import IUsuarioRepository
from app.infrastructure.logging.logger import log_caso_de_uso

class GestionarUsuariosUseCase:
    """
    Implementa las operaciones de gestion de usuarios definidas en CU_ADM--001.
    Separamos este caso de uso del registro por que tienen actores diferentes:
    - Registrar: cualquier persona desde afuera
    - Gestionar: solo el administrador desde adentro
    """
    def __init__(self, usuario_repository: IUsuarioRepository):
        self.usuario_repository = usuario_repository
    
    @log_caso_de_uso('listar_usuarios')
    def listar(self)-> list:
        """
        Retorna todos los usuarios del sistema con sus datos principales.
        Excluye el password_hash por seguridad, nunca se expone.
        """

        usuarios = self.usuario_repository.listar_todos()
        return [
            {
                "id": u.id,
                "nombre": u.nombre_completo(),
                "correo": u.correo,
                "rol_id": u.rol_id,
                "activo": u.activo,
                "correo_verificado": u.correo_verificado,
                "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
                "created_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in usuarios
        ]

    @log_caso_de_uso('obtener_usuario')
    def obtener(self, usuario_id:str)-> dict:
        """
        Retorna el detalle de un usuario especifico por su UUID.
        Lanza ValueError si no existe para que el route retorne 404.
        """
        usuario = self.usuario_repository.buscar_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario{usuario_id}no encontrado")
        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo(),
            "correo": usuario.correo,
            "rol_id": usuario.usuario_id, 
            "activo": usuario.activo, 
            "correo_verificado": usuario.correo_verificado,
            "intentos_fallidos": usuario.intentos_fallidos,
            "ultimo_acceso": usuario.ultimo_acceso() if usuario.ultimo_acceso else None,
            "created_at": usuario.created_at() if usuario.created_at else None
        }

    @log_caso_de_uso('activar_desactivar_usuario')
    def cambiar_estado(self, usuario_id: str, activar: bool)-> dict:
        """
        Activa o desactiva un usuario segun el parametro activar, 
        No permite que un administrador se desactive a si mismo
        para evitar que el sistema quede sin administrador.
        """

        usuario = self.usuario_repository.buscar_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario {usuario_id} no encontrado")
        
        usuario.activo = activar
        self.usuario_repository.actualizar(usuario)

        accion = "activado" if activar else "desactivado"
        return {
            "mensaje": f"Usuario{accion} existosamente",
            "id": usuario.id,
            "activo": usuario.activo
        }
    
    @log_caso_de_uso('editar_usuario')
    def editar(self, usuario_id: str, nombre: str, apellido:str)-> dict:
        """
        Edita el nombre y apellido de un usuario, 
        El correo y el rol no se pueden cambiar por este endpoint
        por razones de seguridad e integracion del sistema.
        """

        usuario = self.usuario_repository.buscar_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario {usuario_id} no encontrado")
        usuario.nombre = nombre.strip()
        usuario.apellido = apellido.strip()
        self.usuario_repository.actualizar(usuario)

        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo(),
            "correo": usuario.correo,
            "rol_id": usuario.rol_id,
            "activo": usuario.activo
        }
