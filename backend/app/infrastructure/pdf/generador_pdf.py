"""
Generador de PDF para la ficha técnica agrícola de AgroCycle.
Usa WeasyPrint para convertir HTML renderizado con Jinja2 a PDF profesional.
Los gráficos se generan con matplotlib como imágenes base64 embebidas.
"""
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.infrastructure.pdf.generador_graficos import (
    grafico_ks_por_etapa,
    grafico_humedad_diaria,
    grafico_gastos_pie,
    grafico_precipitacion_mensual,
    grafico_progreso_ciclo,
)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
TEMPLATE_DIR = BASE_DIR


class GeneradorPDF:
    """
    Responsable de renderizar el template HTML con los datos
    y gráficos de la ficha técnica y convertirlo a PDF con WeasyPrint.
    """

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(['html']),
        )
        self.env.filters['capitalize'] = lambda s: s.capitalize() if s else ''
        self.env.filters['upper']      = lambda s: s.upper() if s else ''
        self.env.filters['round']      = lambda v, n=2: round(float(v), n) if v else 0

    def generar(self, datos: dict) -> bytes:
        """
        Genera el PDF de la ficha técnica.

        Args:
            datos: dict retornado por RecopiladorDatosFicha.recopilar()

        Returns:
            bytes del PDF listo para enviar como respuesta HTTP
        """
        datos['fecha_generacion'] = datetime.now().strftime('%d/%m/%Y %H:%M')

        # Logos como URI file://
        datos['logo_agrocycle'] = self._ruta_a_uri(
            os.path.join(ASSETS_DIR, 'logo_agrocycle.png')
        )
        datos['logo_bosque_seco'] = self._ruta_a_uri(
            os.path.join(ASSETS_DIR, 'sello_bosque_seco.png')
        )

        # Generar gráficos como base64
        datos['grafico_ks'] = grafico_ks_por_etapa(
            datos.get('parametros_tecnicos', {})
        )
        datos['grafico_humedad'] = grafico_humedad_diaria(
            datos.get('humedad_diaria', [])
        )
        datos['grafico_gastos'] = grafico_gastos_pie(
            datos.get('manejo_agronomico', {}).get('gastos_por_categoria', {})
        )
        datos['grafico_precipitacion'] = grafico_precipitacion_mensual(
            datos.get('precipitacion_mensual', [])
        )
        datos['grafico_ciclo'] = grafico_progreso_ciclo(
            datos.get('desarrollo_cultivo', {})
        )

        # Renderizar template
        template = self.env.get_template('template_ficha_tecnica.html')
        html_renderizado = template.render(**datos)

        # Convertir a PDF
        pdf_bytes = HTML(
            string=html_renderizado,
            base_url=TEMPLATE_DIR,
        ).write_pdf()

        return pdf_bytes

    def _ruta_a_uri(self, ruta_absoluta: str) -> str:
        """Convierte ruta absoluta a URI file:// para WeasyPrint."""
        return f"file://{ruta_absoluta}"