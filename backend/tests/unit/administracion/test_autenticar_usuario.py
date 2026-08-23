"""
Tests unitarios — AutenticarUsuarioUseCase
CU-ADM-002: Autenticar Usuario

Valida el flujo completo de autenticacion incluyendo:
- Verificacion de credenciales con bcrypt
- Bloqueo por intentos fallidos
- Verificacion de cuenta activa y correo verificado
- Mensaje generico por seguridad (no revela si el correo existe)

Patron AAA: Arrange / Act / Assert
Sin base de datos — todo mockeado.
"""
import pytest
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
from app.application.use_cases.administracion.autenticar_usuario import (
    AutenticarUsuarioUseCase
)


# ============================================================
# Helpers
# ============================================================

def crear_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=4)  # rounds=4 para velocidad en tests
    ).decode('utf-8')


def crear_usuario_mock(
    activo=True,
    correo_verificado=True,
    bloqueado=False,
    intentos_fallidos=0,
    password='Agrocycle2026!',
):
    """Crea un usuario mock con todos los atributos necesarios."""
    usuario = MagicMock()
    usuario.id = 'uuid-test-agricultor'
    usuario.nombre = 'Cesario'
    usuario.apellido = 'Ramos'
    usuario.correo = 'cesar511ramos@gmail.com'
    usuario.rol_id = 2
    usuario.activo = activo
    usuario.correo_verificado = correo_verificado
    usuario.intentos_fallidos = intentos_fallidos
    usuario.password_hash = crear_hash(password)
    usuario.nombre_completo.return_value = 'Cesario Ramos'

    if bloqueado:
        usuario.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=10)
        usuario.esta_bloqueado.return_value = True
    else:
        usuario.bloqueado_hasta = None
        usuario.esta_bloqueado.return_value = False

    return usuario


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def repo_mock():
    return MagicMock()


@pytest.fixture
def caso_uso(repo_mock):
    return AutenticarUsuarioUseCase(usuario_repository=repo_mock)


# ============================================================
# Tests — Login exitoso
# ============================================================

class TestLoginExitoso:
    """
    Valida el flujo feliz: usuario activo, correo verificado,
    no bloqueado, password correcta.
    """

    def test_login_exitoso_retorna_datos_del_usuario(self, caso_uso, repo_mock):
        # Arrange
        usuario = crear_usuario_mock()
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        resultado = caso_uso.ejecutar(
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!'
        )

        # Assert
        assert resultado['correo'] == 'cesar511ramos@gmail.com'
        assert resultado['rol_id'] == 2
        assert 'id' in resultado
        assert 'nombre' in resultado

    def test_login_exitoso_reinicia_intentos_fallidos(self, caso_uso, repo_mock):
        # Arrange
        usuario = crear_usuario_mock(intentos_fallidos=3)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        caso_uso.ejecutar(
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!'
        )

        # Assert — reiniciar_intentos debe llamarse
        usuario.reiniciar_intentos.assert_called_once()

    def test_login_exitoso_actualiza_ultimo_acceso(self, caso_uso, repo_mock):
        # Arrange
        usuario = crear_usuario_mock()
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        caso_uso.ejecutar(
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!'
        )

        # Assert — el repositorio debe llamarse para guardar el acceso
        repo_mock.actualizar.assert_called_once()

    def test_login_exitoso_retorna_nombre_completo(self, caso_uso, repo_mock):
        # Arrange
        usuario = crear_usuario_mock()
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        resultado = caso_uso.ejecutar(
            correo='cesar511ramos@gmail.com',
            password='Agrocycle2026!'
        )

        # Assert
        assert resultado['nombre'] == 'Cesario Ramos'


# ============================================================
# Tests — Correo no existe
# ============================================================

class TestCorreoNoExiste:
    """
    Cuando el correo no existe el sistema debe retornar un mensaje
    generico sin revelar si el correo existe o no — principio de
    seguridad para evitar enumeracion de usuarios.
    """

    def test_correo_inexistente_lanza_credenciales_invalidas(
        self, caso_uso, repo_mock
    ):
        # Arrange
        repo_mock.buscar_por_correo.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='noexiste@gmail.com',
                password='cualquier_password'
            )
        assert 'invalidas' in str(exc.value).lower()

    def test_mensaje_no_revela_si_correo_existe(self, caso_uso, repo_mock):
        """
        El mensaje de error para correo inexistente debe ser identico
        al de password incorrecta — no debe decir 'correo no encontrado'.
        """
        # Arrange
        repo_mock.buscar_por_correo.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(correo='noexiste@gmail.com', password='pass')
        assert 'correo' not in str(exc.value).lower()
        assert 'no existe' not in str(exc.value).lower()
        assert 'no encontrado' not in str(exc.value).lower()


# ============================================================
# Tests — Password incorrecta
# ============================================================

class TestPasswordIncorrecta:
    """
    Valida el comportamiento cuando la password no coincide.
    Debe incrementar intentos fallidos y bloquear tras 5 intentos.
    """

    def test_password_incorrecta_lanza_credenciales_invalidas(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock()
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='password_incorrecta'
            )
        assert 'invalidas' in str(exc.value).lower()

    def test_password_incorrecta_incrementa_intentos_fallidos(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(intentos_fallidos=0)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='password_incorrecta'
            )

        # Assert
        usuario.incrementar_intentos_fallidos.assert_called_once()

    def test_cinco_intentos_fallidos_bloquea_la_cuenta(
        self, caso_uso, repo_mock
    ):
        """
        Al llegar a MAX_INTENTOS_FALLIDOS=5 se debe establecer
        bloqueado_hasta con 15 minutos en el futuro.
        """
        # Arrange — usuario con 4 intentos previos, este es el quinto
        usuario = crear_usuario_mock(intentos_fallidos=4)
        usuario.incrementar_intentos_fallidos.side_effect = (
            lambda: setattr(usuario, 'intentos_fallidos', 5)
        )
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='password_incorrecta'
            )

        # Assert — debe setearse bloqueado_hasta
        assert usuario.bloqueado_hasta is not None

    def test_mensaje_password_incorrecta_es_generico(
        self, caso_uso, repo_mock
    ):
        """
        El mensaje no debe decir 'password incorrecta' ni 'contraseña'.
        Debe ser identico al de correo inexistente por seguridad.
        """
        # Arrange
        usuario = crear_usuario_mock()
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='incorrecta'
            )
        mensaje = str(exc.value).lower()
        assert 'password' not in mensaje
        assert 'contraseña' not in mensaje


# ============================================================
# Tests — Cuenta bloqueada
# ============================================================

class TestCuentaBloqueada:
    """
    Valida el bloqueo temporal por intentos fallidos excesivos.
    El sistema no debe procesar el login si la cuenta esta bloqueada.
    """

    def test_cuenta_bloqueada_lanza_error_con_hora(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(bloqueado=True)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )
        assert 'bloqueada' in str(exc.value).lower()

    def test_cuenta_bloqueada_no_verifica_password(
        self, caso_uso, repo_mock
    ):
        """
        Si la cuenta está bloqueada el sistema debe fallar antes
        de llegar a verificar la password con bcrypt.
        Esto evita ataques de timing.
        """
        # Arrange
        usuario = crear_usuario_mock(bloqueado=True)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )

        # Assert — actualizar no debe llamarse si está bloqueado
        repo_mock.actualizar.assert_not_called()


# ============================================================
# Tests — Cuenta inactiva
# ============================================================

class TestCuentaInactiva:
    def test_cuenta_inactiva_lanza_error_descriptivo(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(activo=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )
        assert 'desactivada' in str(exc.value).lower()

    def test_cuenta_inactiva_no_verifica_password(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(activo=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )

        # Assert
        repo_mock.actualizar.assert_not_called()


# ============================================================
# Tests — Correo sin verificar
# ============================================================

class TestCorreoSinVerificar:
    def test_correo_no_verificado_lanza_error_descriptivo(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(correo_verificado=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )
        assert 'verificar' in str(exc.value).lower()

    def test_correo_no_verificado_no_actualiza_repositorio(
        self, caso_uso, repo_mock
    ):
        # Arrange
        usuario = crear_usuario_mock(correo_verificado=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act
        with pytest.raises(ValueError):
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )

        # Assert
        repo_mock.actualizar.assert_not_called()


# ============================================================
# Tests — Orden de validaciones
# ============================================================

class TestOrdenValidaciones:
    """
    Valida que las verificaciones ocurran en el orden correcto
    por razones de seguridad y rendimiento.
    Orden: correo → bloqueo → activo → verificado → password
    """

    def test_bloqueo_se_verifica_antes_que_activo(
        self, caso_uso, repo_mock
    ):
        """
        Si la cuenta está bloqueada E inactiva, el mensaje debe
        ser de bloqueo, no de inactividad.
        """
        # Arrange
        usuario = crear_usuario_mock(bloqueado=True, activo=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )
        assert 'bloqueada' in str(exc.value).lower()

    def test_activo_se_verifica_antes_que_correo_verificado(
        self, caso_uso, repo_mock
    ):
        """
        Si la cuenta está inactiva Y el correo sin verificar,
        el mensaje debe ser de inactividad.
        """
        # Arrange
        usuario = crear_usuario_mock(activo=False, correo_verificado=False)
        repo_mock.buscar_por_correo.return_value = usuario

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            caso_uso.ejecutar(
                correo='cesar511ramos@gmail.com',
                password='Agrocycle2026!'
            )
        assert 'desactivada' in str(exc.value).lower()
