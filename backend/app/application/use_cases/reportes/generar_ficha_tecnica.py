"""
CU-REP-001 — Generar ficha técnica agrícola en formato PDF.

Orquesta el recopilador de datos y el generador de PDF
para producir la ficha técnica completa de una temporada_parcela.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.infrastructure.pdf.recopilador_datos_ficha import RecopiladorDatosFicha
from app.infrastructure.pdf.generador_pdf import GeneradorPDF
from app.infrastructure.logging.logger import log_caso_de_uso


class GenerarFichaTecnicaUseCase:
    """
    Implementa CU-REP-001.

    Responsabilidades:
    1. Verificar que la temporada_parcela pertenece al agricultor
    2. Recopilar todos los datos desde la BD
    3. Generar el PDF y retornarlo como bytes
    """

    def __init__(self, db: Session):
        self.db = db
        self.recopilador = RecopiladorDatosFicha(db)
        self.generador = GeneradorPDF()

    @log_caso_de_uso('CU-REP-001 Generar Ficha Técnica PDF')
    def ejecutar(
        self,
        temporada_parcela_id: str,
        agricultor_id: str,
    ) -> tuple:
        """
        Genera la ficha técnica PDF de una temporada_parcela.

        Args:
            temporada_parcela_id: UUID de la temporada_parcela
            agricultor_id: UUID del usuario autenticado

        Returns:
            tuple (bytes, int) con el PDF y código HTTP
            o tuple (dict, int) con error y código HTTP
        """
        # 1. Recopilar todos los datos de la BD
        datos = self.recopilador.recopilar(
            temporada_parcela_id=temporada_parcela_id,
            agricultor_id=agricultor_id,
        )

        if not datos:
            return {
                'error': 'Temporada de parcela no encontrada o no pertenece al agricultor'
            }, 404

        # 2. Generar el PDF
        try:
            pdf_bytes = self.generador.generar(datos)
        except Exception as e:
            return {
                'error': f'Error al generar el PDF: {str(e)}'
            }, 500

        return pdf_bytes, 200