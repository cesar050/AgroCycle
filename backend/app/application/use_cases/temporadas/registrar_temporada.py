"""
Caso de uso: CU-TEM-OO1 Registrar Temporada.
Una temporada representa una campaña de siembra completa.
El agricultor la abre al inicio de la temporada de lluvia 
y cierra cuando cosecha y registra la produccion real.
"""
from datetime import date
from typing import Optional
from app.domain.entities.temporada import Temporada
from app.domain.repositories.i_temporada_repository import ITemporadaRepository
from app.domain.repositories.i_finca_repository import IFincaRepository
from app.infrastructure.logging.logger import log_caso_de_uso

class RegistrarTemporadaUseCase:
    """
    Implementa CU-TEM-001
    Valida que la finca pertenezca al agricultor y crea la temporada.
    Un agricultor puede tener multiples temporadas pero solo una activa
    por finca a la vez para evitar confusion en los registros 
    """

    def __init__(
            self,
            temporada_repository: ITemporadaRepository,
            finca_repository: IFincaRepository
    ):
        self.temporada_repository = temporada_repository
        self.finca_repository = finca_repository

    @log_caso_de_uso('registrar_temporada')
    def ejecutar(
        self,
        agricultor_id: str,
        finca_id: str,
        cultivo_id: int,
        nombre: str,
        fecha_inicio: date,
        fecha_fin_estimada: Optional[date] = None,
        observaciones: Optional[str] = None
    ) -> dict:
        """
        Registra una nueva temporada de siembra.
        Paso 1: Verifica que la finca exista y pertenezca al agricultor.
        Paso 2: Verifica que no haya otra temporada activa en esa finca.
        Paso 3: Crea y persiste la temporada
        """
        # Paso 1: Verifica finca
        finca = self.finca_repository.buscar_por_id(finca_id)
        if not finca:
            raise ValueError("Finca no encontrada")
        if not finca.es_del_agricultor(agricultor_id):
            raise PermissionError("No tiene permiso para crear temporada en esta finca")

        # Paso 2: Verificar que no haya temporada activa en la misma finca
        temporadas_activas = self.temporada_repository.listar_activas_por_agricultor(agricultor_id)
        for t in temporadas_activas:
            if t.finca_id == finca_id:
                raise ValueError(
                    f"Ya existe una temporada activa en esta finca: '{t.nombre}'"
                    f"Debes cerrarla antes de crear una nueva"
                )
        # Paso 3: Crear temporada 
        nueva_temporada = Temporada(
            agricultor_id=agricultor_id,
            finca_id=finca_id,
            cultivo_id=cultivo_id,
            nombre=nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin_estimada=fecha_fin_estimada,
            observaciones=observaciones
        )
        temporada_guardada = self.temporada_repository.guardar(nueva_temporada)
        return{
            "id": temporada_guardada.id,
            "nombre": temporada_guardada.nombre,
            "finca_id": temporada_guardada.finca_id,
            "cultivo_id": temporada_guardada.cultivo_id,
            "fecha_inicio": temporada_guardada.fecha_inicio.isoformat(),
            "fecha_fin_estimada": temporada_guardada.fecha_fin_estimada.isoformat() if temporada_guardada.fecha_fin_estimada else None,
            "estado": temporada_guardada.estado,
            "created_at": temporada_guardada.created_at.isoformat()
        }