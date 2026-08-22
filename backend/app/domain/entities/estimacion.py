from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Estimacion:
    temporada_parcela_id: str
    valor_qq_ha: float
    algoritmo_usado: str  # 'fao33', 'ridge', 'random_forest', 'ensemble'

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version_modelo_id: Optional[int] = None
    valor_total_qq: Optional[float] = None
    margen_error_porcentaje: Optional[float] = None
    valor_minimo_qq_ha: Optional[float] = None
    valor_maximo_qq_ha: Optional[float] = None
    etapa_fenologica_momento: Optional[str] = None
    dias_desde_siembra_momento: Optional[int] = None
    variables_entrada: Optional[dict] = None
    factores_positivos: Optional[list] = None
    factores_negativos: Optional[list] = None
    fecha_generacion: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def calcular_rango(self) -> None:
        """
        Calcula el rango mínimo y máximo aplicando el margen de error.
        Ejemplo: si estima 80 qq/ha con 15% de error,
        el rango es [68, 92] qq/ha.
        """
        if self.margen_error_porcentaje and self.valor_qq_ha:
            factor = self.margen_error_porcentaje / 100
            self.valor_minimo_qq_ha = round(self.valor_qq_ha * (1 - factor), 2)
            self.valor_maximo_qq_ha = round(self.valor_qq_ha * (1 + factor), 2)