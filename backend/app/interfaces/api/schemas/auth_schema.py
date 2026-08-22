"""
Esquemas de validación para el módulo de autenticación.
Valida y sanitiza los datos de entrada antes de llegar a los casos de uso.
Pertenece a la capa de interfaces — es la primera línea de defensa.
"""
import re
from dataclasses import dataclass
from typing import Optional


def validar_correo(correo: str) -> bool:
    """
    Valida que el correo tenga formato real con dominio válido.
    Acepta: usuario@gmail.com, usuario@empresa.com.ec, etc.
    Rechaza: usuario@, @gmail, usuario, usuario@.com
    """
    patron = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, correo))


def validar_password(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla requisitos mínimos de seguridad.
    Retorna (True, "") si es válida o (False, "motivo") si no lo es.

    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial: !@#$%^&*
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"

    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe tener al menos una letra mayúscula"

    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe tener al menos una letra minúscula"

    if not re.search(r'\d', password):
        return False, "La contraseña debe tener al menos un número"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe tener al menos un carácter especial: !@#$%^&*"

    return True, ""


def validar_nombre(nombre: str) -> tuple[bool, str]:
    """
    Valida que el nombre solo contenga letras, espacios y tildes.
    Rechaza números, símbolos y nombres vacíos.
    """
    nombre = nombre.strip()
    if len(nombre) < 2:
        return False, "El nombre debe tener al menos 2 caracteres"

    if len(nombre) > 100:
        return False, "El nombre no puede tener más de 100 caracteres"

    patron = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$'
    if not re.match(patron, nombre):
        return False, "El nombre solo puede contener letras y espacios"

    return True, ""


def validar_datos_registro(datos: dict) -> tuple[bool, dict]:
    """
    Valida todos los campos del formulario de registro.
    Retorna (True, {}) si todo es válido o (False, {errores}) si hay problemas.
    """
    errores = {}

    # Validar nombre
    nombre = datos.get('nombre', '').strip()
    valido, mensaje = validar_nombre(nombre)
    if not valido:
        errores['nombre'] = mensaje

    # Validar apellido
    apellido = datos.get('apellido', '').strip()
    valido, mensaje = validar_nombre(apellido)
    if not valido:
        errores['apellido'] = mensaje

    # Validar correo
    correo = datos.get('correo', '').strip()
    if not correo:
        errores['correo'] = "El correo es requerido"
    elif not validar_correo(correo):
        errores['correo'] = "El formato del correo no es válido"

    # Validar contraseña
    password = datos.get('password', '')
    if not password:
        errores['password'] = "La contraseña es requerida"
    else:
        valido, mensaje = validar_password(password)
        if not valido:
            errores['password'] = mensaje

    # Validar rol
    rol_id = datos.get('rol_id')
    if rol_id is None:
        errores['rol_id'] = "El rol es requerido"
    elif rol_id not in [1, 2, 3]:
        errores['rol_id'] = "El rol debe ser 1 (admin), 2 (agricultor) o 3 (agrónomo)"

    hay_errores = len(errores) > 0
    return not hay_errores, errores
