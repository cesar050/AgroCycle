from sqlalchemy.orm import Session
from app.infrastructure.models.agricultor_model import AgricultorModel
import uuid

class PgAgricultorRepository: 

    def __init__(self, db: Session):
        self.db = db

    def buscar_por_usuario_id(self, usuario_id:str):
        """
        Busca el perfil de agricultor asociado a un usuario.
        Retorna el modelo o NOne si no existe 
        """
        return self.db.query(AgricultorModel).filter(
            AgricultorModel.usuario_id == uuid.UUID(usuario_id)
        ).first()
    
    def crear(self, usuario_id:str):
        """
        Crea el perfil de agricultor vinculado al usuario.
        Se llama automaticamente cuando un usuario se registra.
        """
        modelo = AgricultorModel(
            id=uuid.uuid4(),
            usuario_id=uuid.UUID(usuario_id)
        )
        self.db.add(modelo)
        self.db.commit()
        self.db.refresh(modelo)
        return modelo