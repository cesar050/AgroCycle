"""
Caso de uso: CU-TEM-005 Registrar Produccion Real al Cosechar.
Cuando el agricultor cosecha registra la produccion real en quintales.
Este dato es el mas importante para la tesis — es el que se compara
contra la estimacion del modelo predictivo en mayo 2027.
"""
from datetime import date
from typing import Optional
from app.domain.repositories.i_temporada_parcela_repository import ITemporadaParcelaRepository
from app.domain.repositories.i_temporada_repository import ITemporadaRepository
from app.infrastructure.logging.logger import configurar_logger, log_caso_de_uso

logger = configurar_logger('registrar_cosecha')


class RegistrarCosechaUseCase:
    """
    Implementa CU-TEM-005.
    Registra la produccion real cosechada y cierra la temporada parcela.
    Calcula automaticamente los indicadores de rendimiento.
    """

    def __init__(
        self,
        temporada_parcela_repository: ITemporadaParcelaRepository,
        temporada_repository: ITemporadaRepository
    ):
        self.tp_repo = temporada_parcela_repository
        self.temporada_repo = temporada_repository

    @log_caso_de_uso('registrar_cosecha')
    def ejecutar(
        self,
        temporada_parcela_id: str,
        agricultor_id: str,
        produccion_real_qq: float,
        fecha_cosecha: date,
        precio_venta_qq: Optional[float] = None,
        volumen_vendido_qq: Optional[float] = None,
        produccion_autoconsumo_qq: Optional[float] = None,
        observaciones: Optional[str] = None
    ) -> dict:
        """
        Registra la cosecha real de una parcela.
        Paso 1: Verificar que la temporada parcela existe y esta activa.
        Paso 2: Registrar produccion real y datos de venta.
        Paso 3: Calcular rendimiento en qq/ha.
        Paso 4: Actualizar estado fenologico a cosecha.
        """
        tp = self.tp_repo.buscar_por_id(temporada_parcela_id)
        if not tp:
            raise ValueError("TemporadaParcela no encontrada")

        temporada = self.temporada_repo.buscar_por_id(tp.temporada_id)
        if not temporada:
            raise ValueError("Temporada no encontrada")
        if not temporada.es_del_agricultor(agricultor_id):
            raise PermissionError("No tienes permiso para registrar esta cosecha")

        # Calcular ingresos totales
        ingresos_totales = None
        if precio_venta_qq and volumen_vendido_qq:
            ingresos_totales = round(precio_venta_qq * volumen_vendido_qq, 2)

        # Actualizar temporada parcela
        tp.produccion_real_qq = produccion_real_qq
        tp.fecha_cosecha = fecha_cosecha
        tp.precio_venta_qq = precio_venta_qq
        tp.volumen_vendido_qq = volumen_vendido_qq
        tp.ingresos_totales = ingresos_totales
        tp.produccion_autoconsumo_qq = produccion_autoconsumo_qq
        tp.estado_fenologico = 'cosecha'
        tp.avance_ciclo_porcentaje = 100.0

        tp_actualizada = self.tp_repo.actualizar(tp)

        logger.info(
            f"Cosecha registrada: {produccion_real_qq} qq "
            f"en temporada_parcela {temporada_parcela_id}"
        )

        return {
            "id": tp_actualizada.id,
            "temporada_id": tp_actualizada.temporada_id,
            "parcela_id": tp_actualizada.parcela_id,
            "produccion_real_qq": tp_actualizada.produccion_real_qq,
            "fecha_cosecha": tp_actualizada.fecha_cosecha.isoformat(),
            "precio_venta_qq": tp_actualizada.precio_venta_qq,
            "volumen_vendido_qq": tp_actualizada.volumen_vendido_qq,
            "ingresos_totales": tp_actualizada.ingresos_totales,
            "produccion_autoconsumo_qq": tp_actualizada.produccion_autoconsumo_qq,
            "estado_fenologico": tp_actualizada.estado_fenologico,
            "mensaje": "Cosecha registrada exitosamente"
        }