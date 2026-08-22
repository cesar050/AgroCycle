from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import uuid


@dataclass
class TemporadaParcela:
    temporada_id: str
    parcela_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    variedad_semilla_id: Optional[int] = None
    fecha_siembra: Optional[date] = None
    densidad_siembra_kg_ha: Optional[float] = None
    cantidad_semilla_kg: Optional[float] = None
    estado_fenologico: str = 'pre_siembra'
    dias_desde_siembra: Optional[int] = None
    avance_ciclo_porcentaje: Optional[float] = None
    produccion_real_qq: Optional[float] = None
    fecha_cosecha: Optional[date] = None
    precio_venta_qq: Optional[float] = None
    volumen_vendido_qq: Optional[float] = None
    ingresos_totales: Optional[float] = None
    produccion_autoconsumo_qq: Optional[float] = None
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def dias_transcurridos(self) -> Optional[int]:
        """
        Calcula los dias transcurridos desde la siembra hasta hoy.
        Retorna None si no hay fecha de siembra registrada.
        """
        if not self.fecha_siembra:
            return None
        return (date.today() - self.fecha_siembra).days

    def actualizar_fenologia(self, variedad_ciclo_dias: int) -> None:
        """
        Actualiza el estado fenologico segun los dias transcurridos.
        Usa el ciclo vegetativo de la variedad de semilla para calcular
        en que etapa del cultivo se encuentra el maiz.
        """
        dias = self.dias_transcurridos()
        if dias is None:
            return

        self.dias_desde_siembra = dias
        self.avance_ciclo_porcentaje = min(
            round((dias / variedad_ciclo_dias) * 100, 1), 100
        )

        porcentaje = self.avance_ciclo_porcentaje
        if porcentaje < 5:
            self.estado_fenologico = 'emergencia'
        elif porcentaje < 30:
            self.estado_fenologico = 'crecimiento_vegetativo'
        elif porcentaje < 55:
            self.estado_fenologico = 'floracion'
        elif porcentaje < 80:
            self.estado_fenologico = 'llenado_grano'
        elif porcentaje < 95:
            self.estado_fenologico = 'maduracion'
        else:
            self.estado_fenologico = 'cosecha'