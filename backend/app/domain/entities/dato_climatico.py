from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class DatoClimatico:
    parcela_id: str
    fecha: date
    precipitacion_mm: float = 0
    temperatura_max_c: Optional[float] = None
    temperatura_min_c: Optional[float] = None
    temperatura_promedio_c: Optional[float] = None
    humedad_relativa_porcentaje: Optional[float] = None
    radiacion_solar_mj_m2: Optional[float] = None
    velocidad_viento_km_h: Optional[float] = None
    evapotranspiracion_mm: Optional[float] = None
    temporada_id: Optional[str] = None
    fuente: str = 'api'
    created_at: datetime = field(default_factory=datetime.utcnow)