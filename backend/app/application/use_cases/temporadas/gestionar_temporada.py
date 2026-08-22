"""
Caso de uso: CU-TEM-002 Gestionar Temporada.
Permite listar, obtener detalle, vincular parcelas y cerrar temporadas.
"""
from datetime import date
from typing import Optional
from app.domain.entities.temporada_parcela import TemporadaParcela
from app.domain.repositories.i_temporada_repository import ITemporadaRepository
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.domain.repositories.i_parcela_repository import IParcelaRepository
from app.infrastructure.logging.logger import log_caso_de_uso


class GestionarTemporadaUseCase:

    def __init__(
        self,
        temporada_repository: ITemporadaRepository,
        temporada_parcela_repository: ITemporadaParcelaRepository,
        parcela_repository: IParcelaRepository
    ):
        self.temporada_repository = temporada_repository
        self.tp_repository = temporada_parcela_repository
        self.parcela_repository = parcela_repository

    @log_caso_de_uso('listar_temporadas')
    def listar(self, agricultor_id: str) -> list:
        """Lista todas las temporadas del agricultor."""
        temporadas = self.temporada_repository.listar_por_agricultor(agricultor_id)
        return [
            {
                "id": t.id,
                "nombre": t.nombre,
                "finca_id": t.finca_id,
                "cultivo_id": t.cultivo_id,
                "fecha_inicio": t.fecha_inicio.isoformat(),
                "fecha_fin_estimada": t.fecha_fin_estimada.isoformat() if t.fecha_fin_estimada else None,
                "fecha_fin_real": t.fecha_fin_real.isoformat() if t.fecha_fin_real else None,
                "estado": t.estado,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in temporadas
        ]

    @log_caso_de_uso('obtener_temporada')
    def obtener(self, temporada_id: str, agricultor_id: str) -> dict:
        """Retorna el detalle de una temporada con sus parcelas vinculadas."""
        temporada = self.temporada_repository.buscar_por_id(temporada_id)
        if not temporada:
            raise ValueError("Temporada no encontrada")
        if not temporada.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para ver esta temporada")

        parcelas_vinculadas = self.tp_repository.listar_por_temporada(temporada_id)

        return {
            "id": temporada.id,
            "nombre": temporada.nombre,
            "finca_id": temporada.finca_id,
            "cultivo_id": temporada.cultivo_id,
            "fecha_inicio": temporada.fecha_inicio.isoformat(),
            "fecha_fin_estimada": temporada.fecha_fin_estimada.isoformat() if temporada.fecha_fin_estimada else None,
            "fecha_fin_real": temporada.fecha_fin_real.isoformat() if temporada.fecha_fin_real else None,
            "estado": temporada.estado,
            "observaciones": temporada.observaciones,
            "parcelas": [
                {
                    "id": tp.id,
                    "parcela_id": tp.parcela_id,
                    "variedad_semilla_id": tp.variedad_semilla_id,
                    "fecha_siembra": tp.fecha_siembra.isoformat() if tp.fecha_siembra else None,
                    "estado_fenologico": tp.estado_fenologico,
                    "dias_desde_siembra": tp.dias_transcurridos(),
                    "avance_ciclo_porcentaje": tp.avance_ciclo_porcentaje
                }
                for tp in parcelas_vinculadas
            ],
            "total_parcelas": len(parcelas_vinculadas)
        }

    @log_caso_de_uso('vincular_parcela_temporada')
    def vincular_parcela(
        self,
        temporada_id: str,
        agricultor_id: str,
        parcela_id: str,
        variedad_semilla_id: Optional[int] = None,
        fecha_siembra: Optional[date] = None,
        densidad_siembra_kg_ha: Optional[float] = None,
        cantidad_semilla_kg: Optional[float] = None
    ) -> dict:
        """
        Vincula una parcela a la temporada para sembrar en ella.
        Una parcela solo puede estar en una temporada activa a la vez.
        """
        temporada = self.temporada_repository.buscar_por_id(temporada_id)
        if not temporada:
            raise ValueError("Temporada no encontrada")
        if not temporada.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para modificar esta temporada")
        if not temporada.esta_activa():
            raise ValueError("Solo se pueden vincular parcelas a temporadas activas")

        parcela = self.parcela_repository.buscar_por_id(parcela_id)
        if not parcela:
            raise ValueError("Parcela no encontrada")

        if self.tp_repository.existe_parcela_en_temporada(parcela_id, temporada_id):
            raise ValueError("Esta parcela ya esta vinculada a esta temporada")

        nueva_tp = TemporadaParcela(
            temporada_id=temporada_id,
            parcela_id=parcela_id,
            variedad_semilla_id=variedad_semilla_id,
            fecha_siembra=fecha_siembra,
            densidad_siembra_kg_ha=densidad_siembra_kg_ha,
            cantidad_semilla_kg=cantidad_semilla_kg
        )

        tp_guardada = self.tp_repository.guardar(nueva_tp)

        return {
            "id": tp_guardada.id,
            "temporada_id": tp_guardada.temporada_id,
            "parcela_id": tp_guardada.parcela_id,
            "variedad_semilla_id": tp_guardada.variedad_semilla_id,
            "fecha_siembra": tp_guardada.fecha_siembra.isoformat() if tp_guardada.fecha_siembra else None,
            "estado_fenologico": tp_guardada.estado_fenologico,
            "mensaje": "Parcela vinculada exitosamente a la temporada"
        }

    @log_caso_de_uso('cerrar_temporada')
    def cerrar(
        self,
        temporada_id: str,
        agricultor_id: str,
        fecha_fin_real: date,
        observaciones: Optional[str] = None
    ) -> dict:
        """
        Cierra una temporada activa registrando la fecha real de fin.
        Una temporada cerrada no puede reabrirse.
        """
        temporada = self.temporada_repository.buscar_por_id(temporada_id)
        if not temporada:
            raise ValueError("Temporada no encontrada")
        if not temporada.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para cerrar esta temporada")
        if not temporada.puede_cerrar():
            raise ValueError(f"La temporada ya esta {temporada.estado} y no puede cerrarse")

        temporada.estado = 'cerrada'
        temporada.fecha_fin_real = fecha_fin_real
        if observaciones:
            temporada.observaciones = observaciones

        temporada_actualizada = self.temporada_repository.actualizar(temporada)

        return {
            "id": temporada_actualizada.id,
            "nombre": temporada_actualizada.nombre,
            "estado": temporada_actualizada.estado,
            "fecha_fin_real": temporada_actualizada.fecha_fin_real.isoformat(),
            "mensaje": "Temporada cerrada exitosamente"
        }