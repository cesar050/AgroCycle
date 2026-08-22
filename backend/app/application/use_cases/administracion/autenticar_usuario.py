"""
Caso de uso: CU-ADM-002 Autenticar Usuario.
Logica de negocio del login con verificacion de correo obligatoria.
"""
from datetime import datetime, timedelta
import bcrypt
from app.domain.repositories.i_usuario_repository import IUsuarioRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class AutenticarUsuarioUseCase:

    MAX_INTENTOS_FALLIDOS = 5
    MINUTOS_BLOQUEO = 15

    def __init__(self, usuario_repository: IUsuarioRepository):
        self.usuario_repository = usuario_repository

    @log_caso_de_uso('autenticar_usuario')
    def ejecutar(self, correo: str, password: str) -> dict:
        """
        Ejecuta el flujo de autenticacion completo.
        Paso 1: Buscar usuario por correo.
        Paso 2: Verificar bloqueo por intentos fallidos.
        Paso 3: Verificar que la cuenta este activa.
        Paso 4: Verificar que el correo este verificado.
        Paso 5: Verificar contrasena con bcrypt.
        Paso 6: Login exitoso, reiniciar intentos y registrar acceso.
        """
        usuario = self.usuario_repository.buscar_por_correo(correo)

        # Mensaje generico por seguridad — no revelamos si el correo existe
        if not usuario:
            raise ValueError("Credenciales invalidas")

        if usuario.esta_bloqueado():
            raise ValueError(
                f"Cuenta bloqueada temporalmente. "
                f"Intente despues de las {usuario.bloqueado_hasta.strftime('%H:%M')}"
            )

        if not usuario.activo:
            raise ValueError("Cuenta desactivada. Contacte al administrador")

        if not usuario.correo_verificado:
            raise ValueError(
                "Debes verificar tu correo electronico antes de iniciar sesion. "
                "Revisa tu bandeja de entrada."
            )

        password_valida = bcrypt.checkpw(
            password.encode('utf-8'),
            usuario.password_hash.encode('utf-8')
        )

        if not password_valida:
            usuario.incrementar_intentos_fallidos()
            if usuario.intentos_fallidos >= self.MAX_INTENTOS_FALLIDOS:
                usuario.bloqueado_hasta = datetime.utcnow() + timedelta(
                    minutes=self.MINUTOS_BLOQUEO
                )
            self.usuario_repository.actualizar(usuario)
            raise ValueError("Credenciales invalidas")

        usuario.reiniciar_intentos()
        usuario.ultimo_acceso = datetime.utcnow()
        self.usuario_repository.actualizar(usuario)

        return {
            "id": usuario.id,
            "nombre": usuario.nombre_completo(),
            "correo": usuario.correo,
            "rol_id": usuario.rol_id
        }
