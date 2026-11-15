import { Pipe, PipeTransform } from '@angular/core';

export interface EtapaInfo {
  key: string;
  label: string;
  color: string;
  mensaje: string;
}

// Orden real del ciclo fenológico del maíz tal como lo registra el backend
// en estado_fenologico. "sin_etapa" no es una clave real de la BD: es el
// valor de respaldo cuando la parcela no tiene temporada activa.
export const ETAPAS_FENOLOGICAS: EtapaInfo[] = [
  {
    key: 'pre_siembra',
    label: 'Pre-siembra',
    color: '#5E3B1E',
    mensaje: 'El terreno está preparado pero aún no tiene un cultivo activo registrado.',
  },
  {
    key: 'emergencia',
    label: 'Emergencia',
    color: '#7FBF3F',
    mensaje: 'Las primeras plántulas están emergiendo del suelo.',
  },
  {
    key: 'crecimiento_vegetativo',
    label: 'Crecimiento',
    color: '#4E9F3D',
    mensaje: 'Tu cultivo se encuentra en etapa de desarrollo vegetativo.',
  },
  {
    key: 'floracion',
    label: 'Floración',
    color: '#2E7D32',
    mensaje: 'El cultivo está en floración, una etapa sensible al estrés hídrico y a plagas.',
  },
  {
    key: 'llenado_grano',
    label: 'Llenado de grano',
    color: '#E8C547',
    mensaje: 'El grano está en llenado. El riego y la nutrición son claves en esta etapa.',
  },
  {
    key: 'maduracion',
    label: 'Maduración',
    color: '#D4A017',
    mensaje: 'El cultivo está madurando y pronto estará listo para la cosecha.',
  },
  {
    key: 'cosecha',
    label: 'Cosecha',
    color: '#D4A017',
    mensaje: 'La parcela se encuentra en etapa de cosecha.',
  },
];

export const ETAPA_SIN_TEMPORADA: EtapaInfo = {
  key: 'sin_etapa',
  label: 'Sin temporada',
  color: '#ADB5BD',
  mensaje: 'Esta parcela no tiene una temporada de cultivo activa registrada.',
};

const INDICE: Record<string, EtapaInfo> = Object.fromEntries(
  ETAPAS_FENOLOGICAS.map(e => [e.key, e])
);

export function infoEtapa(key: string | null | undefined): EtapaInfo {
  if (!key) return ETAPA_SIN_TEMPORADA;
  return INDICE[key] ?? ETAPA_SIN_TEMPORADA;
}

export function siguienteEtapa(key: string | null | undefined): EtapaInfo | null {
  if (!key) return null;
  const idx = ETAPAS_FENOLOGICAS.findIndex(e => e.key === key);
  if (idx === -1 || idx === ETAPAS_FENOLOGICAS.length - 1) return null;
  return ETAPAS_FENOLOGICAS[idx + 1];
}

type PropiedadEtapa = 'label' | 'color' | 'mensaje';

@Pipe({ name: 'etapaFenologica', standalone: true, pure: true })
export class EtapaFenologicaPipe implements PipeTransform {
  transform(value: string | null | undefined, prop: PropiedadEtapa = 'label'): string {
    return infoEtapa(value)[prop];
  }
}
