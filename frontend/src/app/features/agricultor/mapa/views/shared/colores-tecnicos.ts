// Paleta de 3 bandas para los mapas de calor coropléticos de las vistas
// técnicas dedicadas (pendiente / humedad). Deliberadamente separada de
// mapa.utils.ts: ese archivo alimenta la vista "Mapa normal" (escala de
// 5 tonos) y no se toca — estas vistas usan su propio esquema reducido
// rojo / verde / azul, pedido explícitamente para la defensa de tesis.
export const ROJO_TECNICO  = '#DC2626';
export const VERDE_TECNICO = '#15803D';
export const AZUL_TECNICO  = '#2563EB';

// ----------------------------------------------------------------
// Humedad del suelo (FAO-56): déficit / óptimo / exceso-drenaje
// ----------------------------------------------------------------
export function colorHumedadTecnico(normalizado: number): string {
  if (normalizado < 0.3) return ROJO_TECNICO;
  if (normalizado > 0.7) return AZUL_TECNICO;
  return VERDE_TECNICO;
}

export function clasificacionHumedad(normalizado: number): 'Déficit hídrico' | 'Óptimo' | 'Exceso / drenaje' {
  if (normalizado < 0.3) return 'Déficit hídrico';
  if (normalizado > 0.7) return 'Exceso / drenaje';
  return 'Óptimo';
}

// ----------------------------------------------------------------
// Ks_final bidireccional (FAO-56) = min(Ks_déficit, Ks_exceso).
// La dirección del estrés (si lo hay) se decide por cuál de los dos
// componentes es el más bajo — el mismo criterio que usa el backend
// en CalcularKsSueloUseCase._clasificar.
// ----------------------------------------------------------------
export function colorKsFinalTecnico(ksFinal: number, ksDeficit: number, ksExceso: number): string {
  if (ksFinal >= 0.95) return VERDE_TECNICO;
  return ksDeficit <= ksExceso ? ROJO_TECNICO : AZUL_TECNICO;
}

export function clasificacionKsFinal(ksFinal: number, ksDeficit: number, ksExceso: number): 'Sin estrés hídrico' | 'Estrés por déficit' | 'Estrés por exceso' {
  if (ksFinal >= 0.95) return 'Sin estrés hídrico';
  return ksDeficit <= ksExceso ? 'Estrés por déficit' : 'Estrés por exceso';
}

// ----------------------------------------------------------------
// Pendiente del terreno: convención agronómica — terreno muy plano
// concentra agua (riesgo de drenaje pobre), pendiente fuerte concentra
// riesgo de erosión/escorrentía; la banda intermedia es la manejable.
// ----------------------------------------------------------------
export function colorPendienteTecnico(pendiente: number): string {
  if (pendiente < 5) return AZUL_TECNICO;
  if (pendiente > 25) return ROJO_TECNICO;
  return VERDE_TECNICO;
}

export function clasificacionPendiente(pendiente: number): 'Riesgo de drenaje pobre' | 'Riesgo de erosión' | 'Óptima para manejo agrícola' {
  if (pendiente < 5) return 'Riesgo de drenaje pobre';
  if (pendiente > 25) return 'Riesgo de erosión';
  return 'Óptima para manejo agrícola';
}
