"""
Caso de uso: Registrar Actividad Agricola.
Registra cualquier labor realizada en la parcela durante la temporada.
Maneja: riego, fertilizacion, control fitosanitario y mano de obra.
Cada tipo tiene su detalle especifico que se guarda en tabla separada.
"""
from datetime import date
from typing import Optional
import uuid as uuid_lib
from sqlalchemy import text
from app.domain.entities.actividad import Actividad
from app.domain.repositories.i_actividad_repository import IActividadRepository
from app.domain.repositories.i_dato_climatico_repository import IDatoClimaticoRepository
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('registrar_actividad')


class RegistrarActividadUseCase:

    APORTE_RIEGO_MM_HORA = {
        'perdido': 6.0,
        'aspersion': 4.0,
        'goteo': 2.0
    }

    def __init__(
        self,
        actividad_repository: IActividadRepository,
        dato_climatico_repository: IDatoClimaticoRepository,
        db
    ):
        self.actividad_repo = actividad_repository
        self.clima_repo = dato_climatico_repository
        self.db = db

    @log_caso_de_uso('registrar_actividad')
    def ejecutar(
        self,
        temporada_id: str,
        temporada_parcela_id: str,
        tipo_actividad_id: int,
        fecha: date,
        usuario_id: str,
        descripcion: str = None,
        observaciones: str = None,
        costo_total: float = 0,
        parcela_id: str = None,
        # Datos riego
        tipo_riego: str = None,
        duracion_horas: float = None,
        porcentaje_parcela_regada: float = 100,
        # Datos fertilizacion
        insumo_id: int = None,
        insumo_personalizado: str = None,
        dosis_kg_ha: float = None,
        metodo_aplicacion: str = None,
        costo_unitario: float = None,
        # Datos fitosanitario
        tipo_control: str = None,
        dosis_aplicada: float = None,
        motivo: str = None,
        incidencia_porcentaje: float = None,
        condicion_humedad_momento: float = None,
        condicion_temperatura_momento: float = None,
        efectividad_observada: str = None,
        # Datos mano de obra
        tipo_labor: str = None,
        numero_personas: int = 1,
        dias_trabajados: float = None,
        costo_jornal: float = None,
        es_mano_obra_propia: bool = False
    ) -> dict:
        """
        Registra una actividad agricola con su detalle especifico.
        tipo_actividad_id:
            1 = Preparacion del terreno
            2 = Siembra
            3 = Fertilizacion
            4 = Control fitosanitario
            5 = Riego
            6 = Mano de obra
            7 = Cosecha
            8 = Monitoreo
            9 = Otro
        """
        nueva_actividad = Actividad(
            temporada_id=temporada_id,
            temporada_parcela_id=temporada_parcela_id,
            tipo_actividad_id=tipo_actividad_id,
            fecha=fecha,
            descripcion=descripcion,
            observaciones=observaciones,
            costo_total=costo_total or 0,
            registrado_por=usuario_id
        )

        actividad_guardada = self.actividad_repo.guardar(nueva_actividad)
        detalle = None

        # Riego
        if tipo_actividad_id == 5 and tipo_riego and duracion_horas:
            aporte_por_hora = self.APORTE_RIEGO_MM_HORA.get(tipo_riego, 4.0)
            aporte_hidrico_mm = round(
                aporte_por_hora * duracion_horas * (porcentaje_parcela_regada / 100), 2
            )
            self.db.execute(
                text("""
                    INSERT INTO riegos
                    (id, actividad_id, tipo_riego, duracion_horas,
                     porcentaje_parcela_regada, aporte_hidrico_estimado_mm)
                    VALUES (
                        :id, CAST(:actividad_id AS uuid), :tipo_riego,
                        :duracion_horas, :porcentaje, :aporte
                    )
                """),
                {
                    "id": str(uuid_lib.uuid4()),
                    "actividad_id": actividad_guardada.id,
                    "tipo_riego": tipo_riego,
                    "duracion_horas": duracion_horas,
                    "porcentaje": porcentaje_parcela_regada,
                    "aporte": aporte_hidrico_mm
                }
            )
            self.db.commit()
            if parcela_id:
                self.clima_repo.actualizar_precipitacion(
                    parcela_id, fecha, aporte_hidrico_mm
                )
            detalle = {"aporte_hidrico_mm": aporte_hidrico_mm}
            logger.info(
                f"Riego: {duracion_horas}h {tipo_riego} "
                f"= {aporte_hidrico_mm}mm en {porcentaje_parcela_regada}%"
            )

        # Fertilizacion
        elif tipo_actividad_id == 3 and dosis_kg_ha:
            self.db.execute(
                text("""
                    INSERT INTO fertilizaciones
                    (id, actividad_id, insumo_id, insumo_personalizado,
                     dosis_kg_ha, metodo_aplicacion, costo_unitario)
                    VALUES (
                        :id, CAST(:actividad_id AS uuid), :insumo_id,
                        :insumo_personalizado, :dosis, :metodo, :costo_unitario
                    )
                """),
                {
                    "id": str(uuid_lib.uuid4()),
                    "actividad_id": actividad_guardada.id,
                    "insumo_id": insumo_id,
                    "insumo_personalizado": insumo_personalizado,
                    "dosis": dosis_kg_ha,
                    "metodo": metodo_aplicacion,
                    "costo_unitario": costo_unitario
                }
            )
            self.db.commit()
            detalle = {
                "dosis_kg_ha": dosis_kg_ha,
                "insumo": insumo_personalizado or str(insumo_id)
            }
            logger.info(f"Fertilizacion: {dosis_kg_ha} kg/ha")

        # Control fitosanitario
        elif tipo_actividad_id == 4 and tipo_control:
            self.db.execute(
                text("""
                    INSERT INTO controles_fitosanitarios
                    (id, actividad_id, tipo_control, insumo_id,
                     insumo_personalizado, dosis_aplicada, metodo_aplicacion,
                     motivo, incidencia_porcentaje, condicion_humedad_momento,
                     condicion_temperatura_momento, efectividad_observada)
                    VALUES (
                        :id, CAST(:actividad_id AS uuid), :tipo_control,
                        :insumo_id, :insumo_personalizado, :dosis, :metodo,
                        :motivo, :incidencia, :humedad, :temperatura, :efectividad
                    )
                """),
                {
                    "id": str(uuid_lib.uuid4()),
                    "actividad_id": actividad_guardada.id,
                    "tipo_control": tipo_control,
                    "insumo_id": insumo_id,
                    "insumo_personalizado": insumo_personalizado,
                    "dosis": dosis_aplicada,
                    "metodo": metodo_aplicacion,
                    "motivo": motivo,
                    "incidencia": incidencia_porcentaje,
                    "humedad": condicion_humedad_momento,
                    "temperatura": condicion_temperatura_momento,
                    "efectividad": efectividad_observada
                }
            )
            self.db.commit()
            detalle = {
                "tipo_control": tipo_control,
                "incidencia_porcentaje": incidencia_porcentaje
            }
            logger.info(f"Control fitosanitario: {tipo_control}")

        # Mano de obra
        elif tipo_actividad_id == 6 and tipo_labor and dias_trabajados and costo_jornal:
            costo_total_mo = round(numero_personas * dias_trabajados * costo_jornal, 2)
            self.db.execute(
                text("""
                    INSERT INTO mano_obra
                    (id, actividad_id, tipo_labor, numero_personas,
                     dias_trabajados, costo_jornal, costo_total, es_mano_obra_propia)
                    VALUES (
                        :id, CAST(:actividad_id AS uuid), :tipo_labor,
                        :personas, :dias, :jornal, :costo_total, :es_propia
                    )
                """),
                {
                    "id": str(uuid_lib.uuid4()),
                    "actividad_id": actividad_guardada.id,
                    "tipo_labor": tipo_labor,
                    "personas": numero_personas,
                    "dias": dias_trabajados,
                    "jornal": costo_jornal,
                    "costo_total": costo_total_mo,
                    "es_propia": es_mano_obra_propia
                }
            )
            self.db.commit()
            detalle = {
                "tipo_labor": tipo_labor,
                "numero_personas": numero_personas,
                "dias_trabajados": dias_trabajados,
                "costo_total": costo_total_mo
            }
            logger.info(f"Mano de obra: {tipo_labor} ${costo_total_mo}")

        return {
            "id": actividad_guardada.id,
            "temporada_id": temporada_id,
            "temporada_parcela_id": temporada_parcela_id,
            "tipo_actividad_id": tipo_actividad_id,
            "fecha": fecha.isoformat(),
            "descripcion": descripcion,
            "costo_total": costo_total or 0,
            "detalle": detalle,
            "mensaje": "Actividad registrada exitosamente"
        }