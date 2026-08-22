from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class ResultadoFinanciero:
    """
    Resumen financiero consolidado de una temporada agrícola.

    Se calcula automáticamente al cerrar la temporada o
    cuando el agricultor solicita ver su situación financiera.

    La ganancia neta puede ser negativa — eso indica pérdida,
    que es exactamente lo que el sistema debe hacer visible
    para que el agricultor entienda su situación real.
    """
    temporada_id: str
    ingresos_totales: float
    costos_totales: float

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    costo_semillas: float = 0.0
    costo_fertilizantes: float = 0.0
    costo_agroquimicos: float = 0.0
    costo_mano_obra: float = 0.0
    costo_otros: float = 0.0
    ganancia_neta: Optional[float] = None
    margen_rentabilidad_porcentaje: Optional[float] = None
    costo_por_quintal: Optional[float] = None
    precio_venta_promedio_qq: Optional[float] = None
    produccion_total_qq: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def calcular(self, produccion_qq: Optional[float] = None) -> None:
        """
        Calcula ganancia, margen y costo por quintal.

        Args:
            produccion_qq: quintales totales producidos.
                           Necesario para calcular costo por quintal.

        El margen de rentabilidad puede ser negativo si hay pérdida.
        El costo por quintal solo se calcula si hay producción registrada.
        """
        self.ganancia_neta = round(
            self.ingresos_totales - self.costos_totales, 2
        )

        if self.ingresos_totales > 0:
            self.margen_rentabilidad_porcentaje = round(
                (self.ganancia_neta / self.ingresos_totales) * 100, 2
            )
        else:
            self.margen_rentabilidad_porcentaje = 0.0

        if produccion_qq and produccion_qq > 0:
            self.produccion_total_qq = produccion_qq
            self.costo_por_quintal = round(
                self.costos_totales / produccion_qq, 2
            )

    def hay_perdida(self) -> bool:
        """Retorna True si la temporada tuvo pérdida económica."""
        return self.ganancia_neta is not None and self.ganancia_neta < 0

    def resumen_texto(self) -> str:
        """
        Genera interpretación en lenguaje simple para el agricultor.
        Sin tecnicismos — directo al resultado.
        """
        if self.ganancia_neta is None:
            return "Resultado financiero pendiente de calcular."

        if self.ganancia_neta > 0:
            return (
                f"Temporada rentable. Ganancia neta: "
                f"${self.ganancia_neta:.2f}"
            )
        elif self.ganancia_neta == 0:
            return "La temporada cubrió exactamente los costos. Sin ganancia ni pérdida."
        else:
            return (
                f"Temporada con pérdida. Déficit: "
                f"${abs(self.ganancia_neta):.2f}"
            )