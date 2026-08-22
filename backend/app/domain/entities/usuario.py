"""
Entidad de dominio: Usuario
Representa el concepto de usuario en el negocio de AgroCycle.
No depende de ningún framework ni base de datos.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Usuario:
    nombre: str
    apellido: str
    correo: str
    password_hash: str
    rol_id: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    activo: bool = True
    correo_verificado: bool = False
    token_verificacion: Optional[str] = None
    ultimo_acceso: Optional[datetime] = None
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def esta_bloqueado(self) -> bool:
        """Verifica si el usuario está bloqueado por intentos fallidos."""
        if self.bloqueado_hasta is None:
            return False
        return datetime.utcnow() < self.bloqueado_hasta

    def incrementar_intentos_fallidos(self) -> None:
        """Incrementa el contador de intentos fallidos."""
        self.intentos_fallidos += 1

    def reiniciar_intentos(self) -> None:
        """Reinicia el contador tras login exitoso."""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None

    def nombre_completo(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"
