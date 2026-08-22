import {
  Component, Input, OnChanges, SimpleChanges,
  ElementRef, ViewChild, signal, HostListener
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';

interface Punto { x: number; y: number; }

interface FincaSVG {
  nombre:     string;
  puntos:     Punto[];
  centroide:  Punto;
}

interface LoteSVG {
  id:        string;
  nombre:    string;
  area_ha:   number;
  puntos:    Punto[];
  centroide: Punto;
  parcelas:  ParcelaSVG[];
}

interface ParcelaSVG {
  id:                string;
  nombre:            string;
  loteNombre:        string;
  superficie_ha:     number;
  altitud_msnm:      number;
  pendiente:         number;
  orientacion:       string;
  estado_fenologico: string;
  estimacion_qq_ha:  number;
  avance_ciclo:      number;
  produccion_real:   number;
  puntos:            Punto[];
  centroide:         Punto;
  color:             string;
  colorBorde:        string;
}

const COLORES: Record<string, { fill: string; border: string }> = {
  pre_siembra:           { fill: '#5E3B1E', border: '#3E2510' },
  emergencia:            { fill: '#7FBF3F', border: '#5A8C2A' },
  crecimiento_vegetativo:{ fill: '#4E9F3D', border: '#357029' },
  floracion:             { fill: '#2E7D32', border: '#1B5E20' },
  llenado_grano:         { fill: '#E8C547', border: '#B8962A' },
  maduracion:            { fill: '#D4A017', border: '#A07A10' },
  cosecha:               { fill: '#D4A017', border: '#A07A10' },
};
const ETIQUETAS: Record<string, string> = {
  cosecha:               'Cosecha',
  maduracion:            'Maduración',
  llenado_grano:         'Llenado',
  floracion:             'Floración',
  crecimiento_vegetativo:'Crecimiento',
  emergencia:            'Emergencia',
  pre_siembra:           'Pre-siembra',
};

@Component({
  selector: 'app-mapa-finca',
  standalone: true,
  imports: [CommonModule, DecimalPipe],
  templateUrl: './mapa-finca.component.html',
  styleUrl:    './mapa-finca.component.scss',
})
export class MapaFincaComponent implements OnChanges {

  @Input() datos: any    = null;
  @Input() alto:  number = 320;
  @Input() topografia: any    = null;
  @Input() vista: 'normal' | 'pendiente' | 'humedad' = 'normal';

  @ViewChild('svgRef') svgRef!: ElementRef<SVGElement>;

  finca        = signal<FincaSVG | null>(null);
  lotes        = signal<LoteSVG[]>([]);
  tooltipData  = signal<{
    visible: boolean; x: number; y: number; p: ParcelaSVG | null
  }>({ visible: false, x: 0, y: 0, p: null });

  viewBox      = '0 0 600 320';
  totalParcelas = 0;
  nombreFinca   = '';
  private _proj: {
    minLng: number; maxLat: number; scala: number;
    oX: number; oY: number;
  } | null = null;

  // Zoom y pan
  escala  = signal(1);
  transX  = signal(0);
  transY  = signal(0);
  private _drag = false;
  private _lx   = 0;
  private _ly   = 0;

  ngOnChanges(c: SimpleChanges) {
    if (c['datos'] && this.datos?.finca) this.procesar();
  }

  colorTopografia(norm: number): string {
    // Paleta AgroCycle para elevación
    if (norm < 0.2)  return '#1B5E20'; // muy bajo — verde oscuro
    if (norm < 0.4)  return '#388E3C'; // bajo — verde
    if (norm < 0.6)  return '#8BC34A'; // medio — verde claro
    if (norm < 0.8)  return '#FFC107'; // alto — amarillo
    return '#D32F2F';                   // muy alto — rojo (ladera)
  }

  // Genera un gradiente SVG para representar la pendiente
  generarGradienteTopografia(
    parcelaId: string
  ): { stops: string; cx: number; cy: number; r: number } | null {
    if (!this.topografia?.parcelas) return null;
    const datos = this.topografia.parcelas.find(
      (p: any) => p.parcela_id === parcelaId
    );
    if (!datos?.puntos?.length) return null;

    // Encontrar el punto más alto y más bajo
    const puntos = datos.puntos;
    const altMin = datos.altitud_min;
    const altMax = datos.altitud_max;
    const rango  = altMax - altMin || 1;

    // Centroide del gradiente (punto más alto)
    const puntoCumbre = puntos.reduce(
      (max: any, p: any) => p.elevacion > max.elevacion ? p : max,
      puntos[0]
    );

    const cx = this.proyectarLng(puntoCumbre.lng);
    const cy = this.proyectarLat(puntoCumbre.lat);

    // Radio del gradiente basado en la parcela
    const todosLotes = this.lotes();
    let radio = 80;
    todosLotes.forEach(l => {
      l.parcelas.forEach(p => {
        if (p.id === parcelaId && p.puntos.length > 0) {
          const xs = p.puntos.map((pt: Punto) => pt.x);
          const ys = p.puntos.map((pt: Punto) => pt.y);
          const w  = Math.max(...xs) - Math.min(...xs);
          const h  = Math.max(...ys) - Math.min(...ys);
          radio = Math.max(w, h) * 0.7;
        }
      });
    });

    return { stops: '', cx, cy, r: radio };
  }

  // Radio de los puntos de grilla según zoom
  get radioGrilla(): number {
    return Math.max(3, 6 / this.escala());
  }

    // Puntos de topografía proyectados para la parcela
  puntosTopoParcela(parcelaId: string): any[] {
    if (!this.topografia?.parcelas) return [];
    const p = this.topografia.parcelas.find((p: any) => p.parcela_id === parcelaId);
    if (!p?.puntos) return [];

    // Necesitamos los mismos parámetros de proyección
    // Los puntos ya vienen con lat/lng — proyectarlos igual que los polígonos
    return p.puntos;
  }

  private procesar() {
    const finca = this.datos.finca;
    this.nombreFinca = finca.nombre;


    // Recopilar TODAS las coords para el bounding box global
    const todas: [number, number][] = [];

    // Coords de la finca
    if (finca.geojson?.coordinates?.[0]) {
      finca.geojson.coordinates[0].forEach((c: number[]) =>
        todas.push([c[0], c[1]])
      );
    }

    // Coords de lotes y parcelas
    (finca.lotes || []).forEach((l: any) => {
      if (l.geojson?.coordinates?.[0]) {
        l.geojson.coordinates[0].forEach((c: number[]) =>
          todas.push([c[0], c[1]])
        );
      }
      (l.parcelas || []).forEach((p: any) => {
        if (p.geojson?.coordinates?.[0]) {
          p.geojson.coordinates[0].forEach((c: number[]) =>
            todas.push([c[0], c[1]])
          );
        }
      });
    });

    if (!todas.length) return;

    const lngs = todas.map(c => c[0]);
    const lats  = todas.map(c => c[1]);
    const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
    const minLat = Math.min(...lats),  maxLat = Math.max(...lats);

    const geoW = maxLng - minLng || 0.0001;
    const geoH = maxLat - minLat || 0.0001;

    const svgW = 600, svgH = this.alto;
    const pad  = 48;
    const drawW = svgW - pad * 2;
    const drawH = svgH - pad * 2;

    const scala = Math.min(drawW / geoW, drawH / geoH);
    const oX    = pad + (drawW - geoW * scala) / 2;
    const oY    = pad + (drawH - geoH * scala) / 2;

    const proj = (lng: number, lat: number): Punto => ({
      x: oX + (lng - minLng) * scala,
      y: oY + (maxLat - lat) * scala,
    });

    const centroide = (pts: Punto[]): Punto => ({
      x: pts.reduce((s, p) => s + p.x, 0) / pts.length,
      y: pts.reduce((s, p) => s + p.y, 0) / pts.length,
    });

    const toPuntos = (coords: number[][]): Punto[] =>
      coords.map(c => proj(c[0], c[1]));

    this.viewBox = `0 0 ${svgW} ${svgH}`;
    this.escala.set(1); this.transX.set(0); this.transY.set(0);

    // Finca
    let fincaSVG: FincaSVG | null = null;
    if (finca.geojson?.coordinates?.[0]) {
      const pts = toPuntos(finca.geojson.coordinates[0]);
      fincaSVG = { nombre: finca.nombre, puntos: pts, centroide: centroide(pts) };
    }

    // Lotes y parcelas
    let total = 0;
    const lotesSVG: LoteSVG[] = (finca.lotes || []).map((l: any) => {
      const lotePts = l.geojson?.coordinates?.[0]
        ? toPuntos(l.geojson.coordinates[0]) : [];

      const parcelasSVG: ParcelaSVG[] = (l.parcelas || [])
        .filter((p: any) => p.geojson?.coordinates?.[0])
        .map((p: any) => {
          const pts  = toPuntos(p.geojson.coordinates[0]);
          const c    = centroide(pts);
          const etapa = p.estado_fenologico || 'pre_siembra';
          const col   = COLORES[etapa] || COLORES['pre_siembra'];
          total++;
          return {
            id: p.id, nombre: p.nombre, loteNombre: l.nombre,
            superficie_ha: p.superficie_ha,
            altitud_msnm: p.altitud_msnm,
            pendiente: p.pendiente,
            orientacion: p.orientacion || '—',
            estado_fenologico: etapa,
            estimacion_qq_ha: p.estimacion_qq_ha,
            avance_ciclo: p.avance_ciclo,
            produccion_real: p.produccion_real,
            puntos: pts, centroide: c,
            color: col.fill, colorBorde: col.border,
          };
        });

      const todosLosPts = [...lotePts, ...parcelasSVG.flatMap(p => p.puntos)];

      return {
        id: l.id, nombre: l.nombre, area_ha: l.superficie_ha,
        puntos: lotePts,
        centroide: todosLosPts.length ? centroide(todosLosPts) : { x: 0, y: 0 },
        parcelas: parcelasSVG,
      };
    });

    this._proj = { minLng, maxLat, scala, oX, oY };
    this.totalParcelas = total;
    this.finca.set(fincaSVG);
    this.lotes.set(lotesSVG);
  }
  

  toPath(puntos: Punto[]): string {
    if (!puntos.length) return '';
    return 'M ' + puntos.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' L ') + ' Z';
  }

  // Métodos de proyección
  proyectarLng(lng: number): number {
    if (!this._proj) return 0;
    return this._proj.oX + (lng - this._proj.minLng) * this._proj.scala;
  }

  proyectarLat(lat: number): number {
    if (!this._proj) return 0;
    return this._proj.oY + (this._proj.maxLat - lat) * this._proj.scala;
  }

  get transform(): string {
    return `translate(${this.transX()},${this.transY()}) scale(${this.escala()})`;
  }

  onWheel(ev: WheelEvent) {
    ev.preventDefault();
    const f = ev.deltaY > 0 ? 0.85 : 1.18;
    this.escala.update(s => Math.max(0.4, Math.min(10, s * f)));
  }

  zoomIn()    { this.escala.update(s => Math.min(10, +(s * 1.3).toFixed(2))); }
  zoomOut()   { this.escala.update(s => Math.max(0.4, +(s / 1.3).toFixed(2))); }
  resetZoom() { this.escala.set(1); this.transX.set(0); this.transY.set(0); }

  onMouseDown(ev: MouseEvent) {
    this._drag = true; this._lx = ev.clientX; this._ly = ev.clientY;
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(ev: MouseEvent) {
    if (!this._drag) return;
    this.transX.update(x => x + ev.clientX - this._lx);
    this.transY.update(y => y + ev.clientY - this._ly);
    this._lx = ev.clientX; this._ly = ev.clientY;
  }

  @HostListener('document:mouseup')
  stopDrag() { this._drag = false; }

  onEnter(ev: MouseEvent, p: ParcelaSVG) {
    const rect = this.svgRef.nativeElement.getBoundingClientRect();
    this.tooltipData.set({
      visible: true, p,
      x: ev.clientX - rect.left + 14,
      y: ev.clientY - rect.top - 10,
    });
  }

  onMove(ev: MouseEvent) {
    if (!this.tooltipData().visible) return;
    const rect = this.svgRef.nativeElement.getBoundingClientRect();
    this.tooltipData.update(t => ({
      ...t,
      x: ev.clientX - rect.left + 14,
      y: ev.clientY - rect.top - 10,
    }));
  }

  // Agrega este método que calcula el color del polígono según pendiente
  colorPorPendiente(pendientePorcentaje: number): string {
    if (pendientePorcentaje < 5)  return '#2E7D32'; // plano — verde
    if (pendientePorcentaje < 10) return '#8BC34A'; // suave — verde claro
    if (pendientePorcentaje < 20) return '#FFC107'; // moderado — amarillo
    if (pendientePorcentaje < 35) return '#FF5722'; // pronunciado — naranja
    return '#D32F2F';                               // muy pronunciado — rojo
  }

  etiquetaPendiente(p: number): string {
    if (p < 5)  return 'Plano';
    if (p < 10) return 'Suave';
    if (p < 20) return 'Moderado';
    if (p < 35) return 'Pronunciado';
    return 'Muy pronunciado';
  }

  // Flecha de orientación de la pendiente
  flechaOrientacion(orientacion: string): number {
    const angulos: Record<string, number> = {
      norte: 0, noreste: 45, este: 90, sureste: 135,
      sur: 180, suroeste: 225, oeste: 270, noroeste: 315,
    };
    return angulos[orientacion] || 0;
  }

  datosPendenciaParcela(parcelaId: string): any {
    if (!this.topografia?.parcelas) return null;
    return this.topografia.parcelas.find(
      (p: any) => p.parcela_id === parcelaId
    ) || null;
  }
  
  onLeave() { this.tooltipData.update(t => ({ ...t, visible: false })); }

  label(e: string)  { return ETIQUETAS[e] || e; }
  color(e: string)  { return (COLORES[e] || COLORES['pre_siembra']).fill; }

  get leyenda() {
    const s = new Set<string>();
    this.lotes().forEach(l => l.parcelas.forEach(p => s.add(p.estado_fenologico)));
    return Array.from(s).map(e => ({ etapa: e, label: this.label(e), color: this.color(e) }));
  }
}