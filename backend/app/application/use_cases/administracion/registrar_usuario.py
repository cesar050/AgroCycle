"""
Caso de uso: CU_ADM-001 Gestionar Usuarios (flujo de creacion)
Logica de negocio para registrar un nuevo usuario en el sistema.
Al registrarse un usuario con rol agricultor se crea automaticamente
su perfil en la tabla agricultores en la misma operacion.
Al registrarse con rol agronomo se crea su perfil en agronomos.
"""
import bcrypt
from app.domain.entities.usuario import Usuario
from app.domain.repositories.i_usuario_repository import IUsuarioRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class RegistrarUsuarioUseCase:

    def __init__(
        self,
        usuario_repository: IUsuarioRepository,
        agricultor_repository=None,
        agronomo_repository=None,
    ):
        """
        Recibe repositorios por inyeccion de dependencias.
        agricultor_repository y agronomo_repository son opcionales
        para no romper tests existentes.
        """
        self.usuario_repository = usuario_repository
        self.agricultor_repository = agricultor_repository
        self.agronomo_repository = agronomo_repository

    @log_caso_de_uso('registrar_usuario')
    def ejecutar(
        self,
        nombre: str,
        apellido: str,
        correo: str,
        password: str,
        rol_id: int = 2,
        numero_registro: str = None,
        especialidad: str = None,
    ) -> dict:
        """
        Registra un nuevo usuario en el sistema.

        Paso 1: Verifica que el correo no exista
        Paso 2: Hashea la contraseña con bcrypt rounds=12
        Paso 3: Crea la entidad de dominio
        Paso 4: Persiste el usuario
        Paso 5: Si es agricultor (rol_id=2) crea perfil en agricultores
        Paso 6: Si es agronomo (rol_id=3) crea perfil en agronomos

        Args:
            numero_registro: requerido solo para agronomos
            especialidad: opcional para agronomos
        """
        if self.usuario_repository.existe_correo(correo):
            raise ValueError(
                f"El correo {correo} ya está registrado en el sistema"
            )

        # Validar que el agrónomo tenga número de registro
        if rol_id == 3 and not numero_registro:
            raise ValueError(
                "El número de registro profesional es requerido para agronomos"
            )

        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        nuevo_usuario = Usuario(
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            correo=correo.lower().strip(),
            password_hash=password_hash,
            rol_id=rol_id
        )

        usuario_guardado = self.usuario_repository.guardar(nuevo_usuario)

        # Crear perfil según el rol
        if rol_id == 2 and self.agricultor_repository:
            self.agricultor_repository.crear(usuario_guardado.id)

        if rol_id == 3 and self.agronomo_repository:
            self.agronomo_repository.crear(
                usuario_id=usuario_guardado.id,
                numero_registro=numero_registro,
                especialidad=especialidad,
            )

        return {
            'id': usuario_guardado.id,
            'nombre': usuario_guardado.nombre_completo(),
            'correo': usuario_guardado.correo,
            'rol_id': usuario_guardado.rol_id,
            'activo': usuario_guardado.activo,
        }