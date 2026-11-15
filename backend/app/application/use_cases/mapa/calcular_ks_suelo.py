class CalcularKsSueloUseCase:
    """
    Calcula el coeficiente de estres hidrico bidireccional del suelo a
    partir de una lectura instantanea de humedad (m3/m3), devuelto por
    Open-Meteo para el centroide de una parcela.

    A diferencia de CalcularEstresHidricoUseCase (modulo climatico, que
    corre dia a dia sobre una temporada activa y solo modela deficit),
    este caso de uso es puro y sin estado: no depende de una temporada
    ni de BD, y ademas modela el lado simetrico de exceso de humedad
    (suelo encharcado / sin oxigeno para la raiz), que no existe en
    ningun otro punto del sistema.

    Ks_deficit cae a 0 conforme la humedad se acerca al punto de
    marchitez permanente. Ks_exceso cae a 0 conforme la humedad se
    acerca a la saturacion (encharcamiento). Ks_final es el minimo de
    ambos: el suelo nunca esta mejor que la peor de las dos condiciones.
    """

    TIPO_SUELO_DEFECTO = 6

    # Umbrales de humedad volumetrica (m3/m3) por textura de suelo.
    # PUNTO_MARCHITEZ y CAPACIDAD_CAMPO son coherentes con
    # AGUA_DISPONIBLE_SUELO de CalcularEstresHidricoUseCase (mismas 6
    # texturas, mismos ids 1-6) expresado en fraccion volumetrica en
    # vez de mm/m. SATURACION es el punto en el que el suelo queda
    # completamente encharcado (sin aire en los poros).
    PUNTO_MARCHITEZ_M3M3 = {1: 0.10, 2: 0.19, 3: 0.15, 4: 0.24, 5: 0.08, 6: 0.14}
    CAPACIDAD_CAMPO_M3M3 = {1: 0.22, 2: 0.41, 3: 0.33, 4: 0.52, 5: 0.16, 6: 0.34}
    SATURACION_M3M3 = {1: 0.40, 2: 0.48, 3: 0.46, 4: 0.55, 5: 0.38, 6: 0.44}

    FRACCION_AGUA_DISPONIBLE = 0.55

    def calcular(self, humedad_m3m3: float, tipo_suelo_id: int = None) -> dict:
        tipo_suelo = tipo_suelo_id or self.TIPO_SUELO_DEFECTO
        wp = self.PUNTO_MARCHITEZ_M3M3.get(tipo_suelo, 0.14)
        fc = self.CAPACIDAD_CAMPO_M3M3.get(tipo_suelo, 0.34)
        sat = self.SATURACION_M3M3.get(tipo_suelo, 0.44)

        ks_deficit = self._calcular_ks_deficit(humedad_m3m3, wp, fc)
        ks_exceso = self._calcular_ks_exceso(humedad_m3m3, fc, sat)
        ks_final = round(min(ks_deficit, ks_exceso), 3)

        return {
            'ks_deficit': ks_deficit,
            'ks_exceso': ks_exceso,
            'ks_final': ks_final,
            'nivel_estres': self._clasificar(ks_final, ks_deficit, ks_exceso),
        }

    def _calcular_ks_deficit(self, humedad: float, wp: float, fc: float) -> float:
        umbral = fc - self.FRACCION_AGUA_DISPONIBLE * (fc - wp)
        if humedad >= umbral:
            return 1.0
        if humedad <= wp:
            return 0.0
        return round((humedad - wp) / (umbral - wp), 3)

    def _calcular_ks_exceso(self, humedad: float, fc: float, sat: float) -> float:
        if humedad <= fc:
            return 1.0
        if humedad >= sat:
            return 0.0
        return round((sat - humedad) / (sat - fc), 3)

    def _clasificar(self, ks_final: float, ks_deficit: float, ks_exceso: float) -> str:
        if ks_final >= 1.0:
            return 'sin_estres'
        direccion = 'deficit' if ks_deficit <= ks_exceso else 'exceso'
        if ks_final >= 0.75:
            return f'estres_{direccion}_leve'
        if ks_final >= 0.50:
            return f'estres_{direccion}_moderado'
        return f'estres_{direccion}_severo'
