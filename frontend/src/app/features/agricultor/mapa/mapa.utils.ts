// ================================================================
// Shapes exactas devueltas por el backend (confirmadas contra
// backend/app/interfaces/api/routes/lotes_parcelas_routes.py).
// No agregar campos que el backend no envía todavía.
// ================================================================
export interface Parcela {
  id: string;
  nombre: string;
  superficie_ha: number;
  altitud_msnm: number;
  pendiente: number;
  orientacion: string | null;
  estado_fenologico: string | null;
  avance_ciclo: number;
  produccion_real: number;
  estimacion_qq_ha: number;
  geojson: any;
}

export interface Lote {
  id: string;
  nombre: string;
  superficie_ha: number;
  geojson: any;
  parcelas: Parcela[];
}

export interface Finca {
  id: string;
  nombre: string;
  superficie_ha: number;
  provincia?: string | null;
  canton?: string | null;
  sector?: string | null;
  geojson: any;
  lotes: Lote[];
}

export interface TopografiaParcela {
  parcela_id: string;
  nombre: string;
  superficie_ha: number;
  altitud_min: number;
  altitud_max: number;
  altitud_prom: number;
  pendiente: number;
  puntos: { lat: number; lng: number; elevacion: number; normalizado: number }[];
  geojson: any;
}

export interface HumedadParcela {
  parcela_id: string;
  nombre: string;
  humedad_m3m3: number;
  normalizado: number;
  // Estrés hídrico bidireccional (Ks_final = min(Ks_déficit, Ks_exceso)),
  // calculado en el backend por CalcularKsSueloUseCase a partir del tipo
  // de suelo real de la parcela.
  ks_deficit?: number;
  ks_exceso?: number;
  ks_final?: number;
  nivel_estres?: string;
}

// ================================================================
// ESTADO SEMÁFORO DE LA PARCELA (panel izquierdo + chip "requieren atención")
// Cadena de prioridad: primero los estados de ciclo, luego las señales
// de alerta que sí tenemos disponibles sin pedir APIs nuevas (humedad
// de /mapa/humedad cuando esa capa ya fue cargada, y pendiente del propio
// /mapa). Si ninguna señal de alerta aplica, es "Buen estado".
// ================================================================
export type TonoEstado = 'verde' | 'amarillo' | 'rojo' | 'gris';

export interface EstadoParcela {
  label: string;
  color: string;
  tono: TonoEstado;
}

const COLOR_TONO: Record<TonoEstado, string> = {
  verde: '#4CAF50',
  amarillo: '#FFC107',
  rojo: '#F44336',
  gris: '#9E9E9E',
};

export function calcularEstadoParcela(
  parcela: Parcela,
  humedad?: HumedadParcela,
): EstadoParcela {
  if (!parcela.estado_fenologico) {
    return { label: 'Sin temporada', color: COLOR_TONO.gris, tono: 'gris' };
  }
  if ((parcela.avance_ciclo ?? 0) >= 100) {
    return { label: 'Cosecha completada', color: COLOR_TONO.verde, tono: 'verde' };
  }
  if (parcela.estado_fenologico === 'cosecha') {
    return { label: 'En cosecha', color: COLOR_TONO.verde, tono: 'verde' };
  }
  if (humedad && humedad.normalizado < 0.3) {
    return { label: 'Revisar agua', color: COLOR_TONO.amarillo, tono: 'amarillo' };
  }
  if ((parcela.pendiente ?? 0) > 30) {
    return { label: 'Atención necesaria', color: COLOR_TONO.rojo, tono: 'rojo' };
  }
  return { label: 'Buen estado', color: COLOR_TONO.verde, tono: 'verde' };
}

// ================================================================
// RECOMENDACIONES LOCALES (panel derecho, "¿Qué debes hacer?")
// Generadas a partir de los mismos datos que ya llegan del backend
// (datosMapa / datosTopografia / datosHumedad) — sin llamar APIs nuevas.
// ================================================================
export interface Recomendacion {
  titulo: string;
  descripcion: string;
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
}

export function generarRecomendaciones(
  parcela: Parcela,
  humedad?: HumedadParcela,
  topo?: TopografiaParcela,
): Recomendacion[] {
  const recs: Recomendacion[] = [];

  if (humedad && humedad.normalizado < 0.3) {
    recs.push({
      titulo: 'Revisar humedad del suelo',
      descripcion: 'La humedad registrada está por debajo del nivel óptimo para el cultivo. Evalúa si conviene programar riego.',
      prioridad: humedad.normalizado < 0.2 ? 'ALTA' : 'MEDIA',
    });
  }

  const pendiente = topo?.pendiente ?? parcela.pendiente ?? 0;
  if (pendiente > 25) {
    recs.push({
      titulo: 'Riesgo de erosión',
      descripcion: 'La pendiente del terreno es pronunciada. Revisa drenajes y considera barreras vivas para evitar pérdida de suelo.',
      prioridad: pendiente > 45 ? 'ALTA' : 'MEDIA',
    });
  }

  if ((parcela.avance_ciclo ?? 0) > 80 && parcela.estado_fenologico !== 'cosecha') {
    recs.push({
      titulo: 'Preparar cosecha',
      descripcion: 'El cultivo está cerca de completar su ciclo. Organiza con anticipación mano de obra y logística de cosecha.',
      prioridad: 'MEDIA',
    });
  }

  if (parcela.estado_fenologico === 'floracion') {
    recs.push({
      titulo: 'Vigilar polinización y plagas',
      descripcion: 'La floración es una etapa sensible al estrés hídrico y a plagas. Monitorea el cultivo con frecuencia.',
      prioridad: 'BAJA',
    });
  }

  if (!parcela.estado_fenologico) {
    recs.push({
      titulo: 'Registrar una temporada',
      descripcion: 'Esta parcela no tiene un ciclo de cultivo activo. Registra una temporada para empezar a dar seguimiento.',
      prioridad: 'BAJA',
    });
  }

  return recs;
}

// ================================================================
// ESCALAS DE COLOR DE CAPAS TEMÁTICAS (migradas del componente original)
// ================================================================
export function colorPendiente(p: number): string {
  if (p < 5) return '#4CAF50';
  if (p < 15) return '#CDDC39';
  if (p < 25) return '#FFC107';
  if (p < 45) return '#FF5722';
  return '#B71C1C';
}

export function etiquetaPendiente(p: number): string {
  if (p < 5) return 'Plana';
  if (p < 15) return 'Suave';
  if (p < 25) return 'Moderada';
  if (p < 45) return 'Fuerte';
  return 'Escarpada';
}

export function colorHumedad(normalizado: number): string {
  const n = normalizado ?? 0;
  if (n < 0.2) return '#D32F2F';
  if (n < 0.4) return '#FF8F00';
  if (n < 0.6) return '#FDD835';
  if (n < 0.8) return '#66BB6A';
  return '#1565C0';
}

function hexARgb(hex: string): { r: number; g: number; b: number } {
  const h = hex.replace('#', '');
  return {
    r: parseInt(h.substring(0, 2), 16),
    g: parseInt(h.substring(2, 4), 16),
    b: parseInt(h.substring(4, 6), 16),
  };
}

function interpolarHex(colorA: string, colorB: string, t: number): string {
  const a = hexARgb(colorA);
  const b = hexARgb(colorB);
  const r = Math.round(a.r + (b.r - a.r) * t);
  const g = Math.round(a.g + (b.g - a.g) * t);
  const bl = Math.round(a.b + (b.b - a.b) * t);
  return `#${[r, g, bl].map(v => v.toString(16).padStart(2, '0')).join('')}`;
}

export function colorElevacion(normalizado: number): string {
  const n = Math.max(0, Math.min(1, normalizado ?? 0));
  if (n < 0.25) return interpolarHex('#2166AC', '#74ADD1', n / 0.25);
  if (n < 0.50) return interpolarHex('#74ADD1', '#FEE08B', (n - 0.25) / 0.25);
  if (n < 0.75) return interpolarHex('#FEE08B', '#F46D43', (n - 0.50) / 0.25);
  return interpolarHex('#F46D43', '#A50026', (n - 0.75) / 0.25);
}

// ================================================================
// GEOMETRÍA — construcción de GeoJSON y cálculo de centro/bounds
// ================================================================
export function construirGeoJSONParcelas(finca: any): any {
  const features = (finca?.lotes || []).flatMap((lote: any) =>
    (lote.parcelas || [])
      .filter((p: any) => p.geojson)
      .map((p: any) => ({
        type: 'Feature',
        properties: { id: p.id, nombre: p.nombre, etapa: p.estado_fenologico },
        geometry: p.geojson,
      }))
  );
  return { type: 'FeatureCollection', features };
}

export function calcularCentro(geojson: any): [number, number] | null {
  const anillo = geojson?.coordinates?.[0];
  if (!anillo?.length) return null;
  const lat = anillo.reduce((s: number, c: number[]) => s + c[1], 0) / anillo.length;
  const lng = anillo.reduce((s: number, c: number[]) => s + c[0], 0) / anillo.length;
  return [lat, lng];
}

export function calcularBounds(geojson: any): [[number, number], [number, number]] | null {
  const anillo = geojson?.coordinates?.[0];
  if (!anillo?.length) return null;
  const lats = anillo.map((c: number[]) => c[1]);
  const lngs = anillo.map((c: number[]) => c[0]);
  return [
    [Math.min(...lats), Math.min(...lngs)],
    [Math.max(...lats), Math.max(...lngs)],
  ];
}

// ================================================================
// DIBUJO DE POLÍGONOS EN EL PANEL DE GESTIÓN (Finca/Lote/Parcela)
// Migrado de las antiguas páginas pages/nueva-finca, nuevo-lote y
// nueva-parcela — una sola copia de cada algoritmo reutilizada por
// los tres paneles embebidos en MapaComponent.
// ================================================================

// Ray casting: anillo es un array de [lng, lat] (formato GeoJSON).
export function puntoDentroDePoligono(
  lat: number,
  lng: number,
  anillo: number[][],
): boolean {
  let dentro = false;
  const n = anillo.length;
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const [xi, yi] = anillo[i];
    const [xj, yj] = anillo[j];
    const intersecta = ((yi > lat) !== (yj > lat)) &&
      (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi);
    if (intersecta) dentro = !dentro;
  }
  return dentro;
}

// Fórmula de Shoelace con proyección equirrectangular aproximada.
// Suficiente para una vista previa en el panel — el área real y
// definitiva siempre la calcula PostGIS en el backend al guardar.
export function calcularAreaHaAprox(puntos: { lat: number; lng: number }[]): number {
  const R = 6371000;
  let area = 0;
  const n = puntos.length;
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    const xi = puntos[i].lng * (Math.PI / 180) * R * Math.cos(puntos[i].lat * Math.PI / 180);
    const yi = puntos[i].lat * (Math.PI / 180) * R;
    const xj = puntos[j].lng * (Math.PI / 180) * R * Math.cos(puntos[j].lat * Math.PI / 180);
    const yj = puntos[j].lat * (Math.PI / 180) * R;
    area += xi * yj - xj * yi;
  }
  const areaM2 = Math.abs(area / 2);
  return Math.round(areaM2 / 10000 * 100) / 100;
}
