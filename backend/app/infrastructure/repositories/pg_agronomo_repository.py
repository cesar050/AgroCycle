from typing import Optional
from sqlalchemy.orm import Session
from app.infrastructure.models.agricultor_model import AgricultorModel
from app.infrastructure.models.agronomo_model import AgronomoModel
import uuid


class PgAgronomoRepository:

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_usuario_id(self, usuario_id: str) -> Optional[AgronomoModel]:
        """
        Busca el perfil de agrónomo asociado a un usuario.
        Retorna el modelo o None si no existe.
        """
        return self.db.query(AgronomoModel).filter(
            AgronomoModel.usuario_id == uuid.UUID(usuario_id)
        ).first()

    def buscar_por_id(self, agronomo_id: str) -> Optional[AgronomoModel]:
        """Busca el perfil de agrónomo por su UUID."""
        return self.db.query(AgronomoModel).filter(
            AgronomoModel.id == uuid.UUID(agronomo_id)
        ).first()

    def crear(
        self,
        usuario_id: str,
        numero_registro: str,
        especialidad: str = None,
    ) -> AgronomoModel:
        """
        Crea el perfil de agrónomo vinculado al usuario.
        Se llama automáticamente cuando un usuario se registra
        con rol agrónomo (rol_id=3).

        numero_registro es el número de registro profesional
        del agrónomo ante el SENESCYT o colegio profesional.
        """
        modelo = AgronomoModel(
            id=uuid.uuid4(),
            usuario_id=uuid.UUID(usuario_id),
            numero_registro=numero_registro,
            especialidad=especialidad,
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return modelo