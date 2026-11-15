import { Component, OnInit, computed, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ClimaticoService } from './services/climatico.service';

// ----------------------------------------------------------------
// Tipos de datos reales devueltos por la API climatica
// ----------------------------------------------------------------
interface ClimaDato {
  fecha: string;
  precipitacion_mm: number | null;
  temperatura_max_c: number | null;
  temperatura_min_c: number | null;
  temperatura_promedio_c: number | null;
  humedad_relativa_porcentaje: number | null;
  evapotranspiracion_mm: number | null;
  fuente: string;
}

interface BalanceDia {
  fecha: string;
  etc_mm: number;
  et0_mm: number;
  humedad_estimada_porcentaje: number;
  clasificacion: string;
  estado_fenologico: string;
}

interface SerieDef {
  cls: string;        // clase CSS que lleva el color (tematizable claro/oscuro)
  label: string;
  values: (number | null)[];
}

interface ChartModel {
  w: number;
  h: number;
  bars: { x: number; y: number; w: number; h: number; cx: number }[];
  lines: { cls: string; d: string }[];
  area: string | null;
  areaCls: string | null;
  endDots: { cls: string; cx: number; cy: number }[];
  yTicks: { v: number; y: number }[];
  xLabels: { x: number; text: string }[];
  bands: { x: number; w: number; cx: number }[];  // zonas de hover
  pad: { l: number; r: number; t: number; b: number };
  empty: boolean;
}

@Component({
  selector: 'app-climatico',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './climatico.component.html',
  styleUrl: './climatico.component.scss'
})
export class ClimaticoComponent implements OnInit {

  // ----- Estado de carga -----
  cargando         = signal(true);
  cargandoSerie    = signal(false);
  cargandoBalance  = signal(false);
  descargando      = signal(false);
  guardandoManual  = signal(false);
  error            = signal('');

  // ----- Selección de parcela -----
  fincas        = signal<any[]>([]);
  parcelas      = signal<any[]>([]);
  parcelaId     = signal('');
  parcelaNombre = signal('');

  // ----- Datos climáticos -----
  climaDatos  = signal<ClimaDato[]>([]);
  resumen     = signal<any>(null);
  historial   = signal<any[]>([]);
  paginacion  = signal<any>(null);
  paginaActual = signal(1);
  forecast    = signal<any[]>([]);
  alertas     = signal<any[]>([]);

  // ----- Temporada activa / FAO-56 -----
  tpId           = signal('');
  fechaSiembra   = signal<string | null>(null);
  estadoFenologico = signal('');
  balanceDatos   = signal<BalanceDia[]>([]);
  totalAlertasBalance = signal(0);
  estres         = signal<any>(null);
  sinTemporada   = signal(false);

  // ----- Hover de gráficos -----
  hoverPrecip = signal<number | null>(null);
  hoverTemp   = signal<number | null>(null);
  hoverEt     = signal<number | null>(null);

  // ----- Formulario de registro manual -----
  mostrarFormManual = signal(false);
  formManual = {
    fecha: '',
    precipitacion_mm: '',
    temperatura_max_c: '',
    temperatura_min_c: '',
    humedad_relativa_porcentaje: '',
    evapotranspiracion_mm: '',
  };

  // Geometría lógica compartida por los SVG (se escala a 100% del contenedor)
  private readonly geom = { w: 760, h: 210, l: 40, r: 16, t: 14, b: 26 };

  constructor(private svc: ClimaticoService) {}

  ngOnInit() { this.cargarFincas(); }

  // ================================================================
  // Datos de la temporada activa filtrados para las series de tiempo
  // ================================================================
  serieClima = computed<ClimaDato[]>(() => {
    const orden = [...this.climaDatos()].sort(
      (a, b) => a.fecha.localeCompare(b.fecha)
    );
    const siembra = this.fechaSiembra();
    if (siembra) {
      return orden.filter(d => d.fecha >= siembra);
    }
    return orden;
  });

  // ================================================================
  // Modelos de gráfico (SVG inline, un solo eje cada uno)
  // ================================================================
  precipChart = computed<ChartModel>(() => {
    const datos = this.serieClima();
    const labels = datos.map(d => d.fecha);
    return this.buildChart(labels, [
      { cls: 's-precip', label: 'Precipitación', values: datos.map(d => d.precipitacion_mm ?? 0) }
    ], { type: 'bar', yMin: 0 });
  });

  tempChart = computed<ChartModel>(() => {
    const datos = this.serieClima();
    const labels = datos.map(d => d.fecha);
    return this.buildChart(labels, [
      { cls: 's-tmax',  label: 'Máx',      values: datos.map(d => d.temperatura_max_c) },
      { cls: 's-tmean', label: 'Promedio', values: datos.map(d => d.temperatura_promedio_c) },
      { cls: 's-tmin',  label: 'Mín',      values: datos.map(d => d.temperatura_min_c) },
    ], { type: 'line' });
  });

  // ETc del cultivo si hay balance FAO-56 calculado; si no, ET0 de referencia.
  usandoEtc = computed(() => this.balanceDatos().length > 0);

  etChart = computed<ChartModel>(() => {
    const balance = this.balanceDatos();
    if (balance.length > 0) {
      const siembra = this.fechaSiembra();
      const b = siembra ? balance.filter(d => d.fecha >= siembra) : balance;
      return this.buildChart(b.map(d => d.fecha), [
        { cls: 's-et', label: 'ETc', values: b.map(d => d.etc_mm) }
      ], { type: 'area', yMin: 0 });
    }
    const datos = this.serieClima();
    return this.buildChart(datos.map(d => d.fecha), [
      { cls: 's-et', label: 'ET₀', values: datos.map(d => d.evapotranspiracion_mm) }
    ], { type: 'area', yMin: 0 });
  });

  // Fuente de datos alineada 1:1 con etChart (para el tooltip de hover)
  etSource = computed<{ fecha: string; val: number | null }[]>(() => {
    const balance = this.balanceDatos();
    if (balance.length > 0) {
      const s = this.fechaSiembra();
      const b = s ? balance.filter(d => d.fecha >= s) : balance;
      return b.map(d => ({ fecha: d.fecha, val: d.etc_mm }));
    }
    return this.serieClima().map(d => ({ fecha: d.fecha, val: d.evapotranspiracion_mm }));
  });

  // Sparkline de humedad del suelo estimada (balance FAO-56)
  humChart = computed<ChartModel>(() => {
    const b = this.balanceDatos();
    return this.buildChart(b.map(d => d.fecha), [
      { cls: 's-hum', label: 'Humedad', values: b.map(d => d.humedad_estimada_porcentaje) }
    ], { type: 'line', yMin: 0, yMax: 100, h: 120 });
  });

  // Estado actual del suelo = último día calculado del balance
  balanceActual = computed(() => {
    const b = this.balanceDatos();
    return b.length ? b[b.length - 1] : null;
  });

  // ================================================================
  // Constructor de modelo de gráfico
  // ================================================================
  private buildChart(
    labelsRaw: string[],
    series: SerieDef[],
    opts: { type: 'bar' | 'line' | 'area'; yMin?: number; yMax?: number; h?: number }
  ): ChartModel {
    const g = this.geom;
    const h = opts.h ?? g.h;
    const pad = { l: g.l, r: g.r, t: g.t, b: g.b };
    const plotW = g.w - pad.l - pad.r;
    const plotH = h - pad.t - pad.b;
    const n = labelsRaw.length;

    const empty: ChartModel = {
      w: g.w, h, bars: [], lines: [], area: null, areaCls: null,
      endDots: [], yTicks: [], xLabels: [], bands: [], pad, empty: true
    };
    if (n === 0) return empty;

    // --- escala Y ---
    const all: number[] = [];
    for (const s of series) for (const v of s.values) if (v !== null && !isNaN(v)) all.push(v);
    if (all.length === 0) return empty;

    let yMin = opts.yMin ?? Math.min(...all);
    let yMax = opts.yMax ?? Math.max(...all);
    if (yMax === yMin) yMax = yMin + 1;
    if (opts.yMax === undefined) yMax += (yMax - yMin) * 0.12;   // aire superior
    const ticks = this.niceTicks(yMin, yMax, 4);
    yMin = Math.min(yMin, ticks[0]);
    yMax = Math.max(yMax, ticks[ticks.length - 1]);

    const xAt = (i: number) => n <= 1 ? pad.l + plotW / 2 : pad.l + plotW * (i / (n - 1));
    const yAt = (v: number) => pad.t + plotH * (1 - (v - yMin) / (yMax - yMin));

    const yTicks = ticks.map(v => ({ v, y: yAt(v) }));

    // --- etiquetas X (máx ~7) ---
    const step = Math.max(1, Math.ceil(n / 7));
    const xLabels: { x: number; text: string }[] = [];
    for (let i = 0; i < n; i += step) {
      xLabels.push({ x: xAt(i), text: labelsRaw[i].slice(5) });
    }

    // --- zonas de hover ---
    const bandW = plotW / Math.max(n - 1, 1);
    const bands = labelsRaw.map((_, i) => {
      const cx = xAt(i);
      const x = Math.max(pad.l, cx - bandW / 2);
      return { x, w: bandW, cx };
    });

    const bars: ChartModel['bars'] = [];
    const lines: ChartModel['lines'] = [];
    const endDots: ChartModel['endDots'] = [];
    let area: string | null = null;
    let areaCls: string | null = null;

    if (opts.type === 'bar') {
      const s = series[0];
      const bw = Math.min(bandW * 0.6, 12);
      s.values.forEach((v, i) => {
        const val = v ?? 0;
        const y = yAt(val);
        const base = yAt(yMin);
        bars.push({ x: xAt(i) - bw / 2, y, w: bw, h: Math.max(0, base - y), cx: xAt(i) });
      });
    } else {
      for (const s of series) {
        const d = this.linePath(s.values, xAt, yAt);
        if (d) lines.push({ cls: s.cls, d });
        // punto final (marcador selectivo)
        for (let i = s.values.length - 1; i >= 0; i--) {
          const v = s.values[i];
          if (v !== null && !isNaN(v)) { endDots.push({ cls: s.cls, cx: xAt(i), cy: yAt(v) }); break; }
        }
      }
      if (opts.type === 'area') {
        const s = series[0];
        area = this.areaPath(s.values, xAt, yAt, yAt(yMin));
        areaCls = s.cls;
      }
    }

    return { w: g.w, h, bars, lines, area, areaCls, endDots, yTicks, xLabels, bands, pad, empty: false };
  }

  private linePath(
    values: (number | null)[],
    xAt: (i: number) => number,
    yAt: (v: number) => number
  ): string | null {
    let d = '';
    let pen = false;
    values.forEach((v, i) => {
      if (v === null || isNaN(v)) { pen = false; return; }
      d += `${pen ? 'L' : 'M'}${xAt(i).toFixed(1)} ${yAt(v).toFixed(1)} `;
      pen = true;
    });
    return d.trim() || null;
  }

  private areaPath(
    values: (number | null)[],
    xAt: (i: number) => number,
    yAt: (v: number) => number,
    baseY: number
  ): string | null {
    const pts: { x: number; y: number }[] = [];
    values.forEach((v, i) => {
      if (v !== null && !isNaN(v)) pts.push({ x: xAt(i), y: yAt(v) });
    });
    if (pts.length < 2) return null;
    let d = `M${pts[0].x.toFixed(1)} ${baseY.toFixed(1)} `;
    for (const p of pts) d += `L${p.x.toFixed(1)} ${p.y.toFixed(1)} `;
    d += `L${pts[pts.length - 1].x.toFixed(1)} ${baseY.toFixed(1)} Z`;
    return d;
  }

  private niceTicks(min: number, max: number, count: number): number[] {
    const range = this.niceNum(max - min, false);
    const stepv = this.niceNum(range / (count - 1), true);
    const graphMin = Math.floor(min / stepv) * stepv;
    const graphMax = Math.ceil(max / stepv) * stepv;
    const out: number[] = [];
    for (let v = graphMin; v <= graphMax + stepv * 0.5; v += stepv) {
      out.push(Math.round(v * 100) / 100);
    }
    return out;
  }

  private niceNum(range: number, round: boolean): number {
    if (range <= 0) return 1;
    const exp = Math.floor(Math.log10(range));
    const frac = range / Math.pow(10, exp);
    let nf: number;
    if (round) {
      nf = frac < 1.5 ? 1 : frac < 3 ? 2 : frac < 7 ? 5 : 10;
    } else {
      nf = frac <= 1 ? 1 : frac <= 2 ? 2 : frac <= 5 ? 5 : 10;
    }
    return nf * Math.pow(10, exp);
  }

  // Posición % para el tooltip HTML sobre el gráfico
  tipLeft(model: ChartModel, i: number): number {
    const b = model.bands[i];
    return b ? (b.cx / model.w) * 100 : 0;
  }

  // ================================================================
  // Carga de parcelas (descubrimiento finca → lote → parcela)
  // ================================================================
  cargarFincas() {
    this.svc.listarFincas().subscribe({
      next: (res) => {
        const fincas = Array.isArray(res) ? res : (res.fincas || []);
        this.fincas.set(fincas);
        if (fincas.length > 0) this.buscarPrimeraParcela(fincas, 0);
        else this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  private buscarPrimeraParcela(fincas: any[], iFinca: number) {
    if (iFinca >= fincas.length) { this.cargando.set(false); return; }
    this.svc.listarLotes(fincas[iFinca].id).subscribe({
      next: (res) => this.buscarEnLotes(fincas, iFinca, res.lotes || res || [], 0),
      error: () => this.buscarPrimeraParcela(fincas, iFinca + 1),
    });
  }

  private buscarEnLotes(fincas: any[], iFinca: number, lotes: any[], iLote: number) {
    if (iLote >= lotes.length) { this.buscarPrimeraParcela(fincas, iFinca + 1); return; }
    this.svc.listarParcelas(lotes[iLote].id).subscribe({
      next: (r) => {
        const p = r.parcelas || r || [];
        if (p.length > 0) {
          this.parcelas.set(p);
          this.seleccionarParcela(p[0].id, p[0].nombre);
        } else {
          this.buscarEnLotes(fincas, iFinca, lotes, iLote + 1);
        }
      },
      error: () => this.buscarEnLotes(fincas, iFinca, lotes, iLote + 1),
    });
  }

  seleccionarParcela(id: string, nombre: string) {
    this.parcelaId.set(id);
    this.parcelaNombre.set(nombre);
    this.resetDatos();
    this.cargarDatos();
  }

  private resetDatos() {
    this.climaDatos.set([]);
    this.resumen.set(null);
    this.balanceDatos.set([]);
    this.estres.set(null);
    this.tpId.set('');
    this.fechaSiembra.set(null);
    this.estadoFenologico.set('');
    this.sinTemporada.set(false);
    this.hoverPrecip.set(null);
    this.hoverTemp.set(null);
    this.hoverEt.set(null);
  }

  cargarDatos() {
    const pid = this.parcelaId();
    if (!pid) return;
    this.cargando.set(true);
    this.cargandoSerie.set(true);

    // Serie completa para los gráficos de tiempo
    this.svc.listarClima(pid).subscribe({
      next: (res) => {
        this.climaDatos.set(res.datos || []);
        this.cargandoSerie.set(false);
        this.cargando.set(false);
      },
      error: () => { this.cargandoSerie.set(false); this.cargando.set(false); },
    });

    // Resumen estadístico + tabla paginada
    this.cargarHistorial(1);

    // Pronóstico 7 días
    this.svc.forecast(pid).subscribe({
      next: (res) => this.forecast.set(res.forecast || []),
      error: () => this.forecast.set([]),
    });

    // Alertas activas (semáforo de urgencia)
    this.svc.generarAlertas().subscribe({
      next: (res) => this.alertas.set(res.alertas || []),
      error: () => this.alertas.set([]),
    });

    // Balance hídrico / estrés FAO-56 (requiere temporada activa)
    this.resolverTemporadaParcela(pid);
  }

  cargarHistorial(pagina: number = 1) {
    this.svc.historialClimatico(this.parcelaId(), { pagina, por_pagina: 12 }).subscribe({
      next: (res) => {
        this.historial.set(res.datos || []);
        this.paginacion.set(res.paginacion || null);
        this.paginaActual.set(pagina);
        if (res.resumen && Object.keys(res.resumen).length) this.resumen.set(res.resumen);
      },
      error: () => {},
    });
  }

  // ================================================================
  // Resolver la temporada_parcela activa de la parcela seleccionada
  // ================================================================
  private resolverTemporadaParcela(pid: string) {
    this.cargandoBalance.set(true);
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const temporadas = (res.temporadas || res || []);
        const activas = temporadas.filter((t: any) => t.estado === 'activa');
        if (activas.length === 0) { this.marcarSinTemporada(); return; }
        this.buscarTpEnTemporadas(pid, activas, 0);
      },
      error: () => this.marcarSinTemporada(),
    });
  }

  private buscarTpEnTemporadas(pid: string, activas: any[], idx: number) {
    if (idx >= activas.length) { this.marcarSinTemporada(); return; }
    this.svc.obtenerTemporada(activas[idx].id).subscribe({
      next: (det) => {
        const tp = (det.parcelas || []).find((p: any) => p.parcela_id === pid);
        if (tp) {
          this.tpId.set(tp.id);
          this.fechaSiembra.set(tp.fecha_siembra || null);
          this.estadoFenologico.set(tp.estado_fenologico || '');
          this.calcularBalance(pid, tp);
        } else {
          this.buscarTpEnTemporadas(pid, activas, idx + 1);
        }
      },
      error: () => this.buscarTpEnTemporadas(pid, activas, idx + 1),
    });
  }

  private calcularBalance(pid: string, tp: any) {
    const hoy = new Date().toISOString().split('T')[0];
    const inicio = tp.fecha_siembra || '2025-12-01';
    const body = { parcela_id: pid, fecha_inicio: inicio, fecha_fin: hoy };

    this.svc.calcularBalanceHidrico(tp.id, body).subscribe({
      next: (res) => {
        this.balanceDatos.set(res.datos || []);
        this.totalAlertasBalance.set(res.total_alertas || 0);
        this.cargandoBalance.set(false);
      },
      error: () => { this.balanceDatos.set([]); this.cargandoBalance.set(false); },
    });

    this.svc.calcularEstresHidrico(tp.id, body).subscribe({
      next: (res) => this.estres.set(res),
      error: () => this.estres.set(null),
    });
  }

  private marcarSinTemporada() {
    this.sinTemporada.set(true);
    this.cargandoBalance.set(false);
  }

  // ================================================================
  // Acciones
  // ================================================================
  descargarDatosHistoricos() {
    const pid = this.parcelaId();
    if (!pid) return;
    this.descargando.set(true);
    const hoy = new Date();
    const inicio = new Date(hoy.getFullYear() - 1, hoy.getMonth(), hoy.getDate());
    this.svc.descargarClima(pid, {
      fecha_inicio: inicio.toISOString().split('T')[0],
      fecha_fin: hoy.toISOString().split('T')[0],
    }).subscribe({
      next: () => { this.descargando.set(false); this.cargarDatos(); },
      error: () => this.descargando.set(false),
    });
  }

  guardarEventoManual() {
    if (!this.formManual.fecha) { this.error.set('La fecha es requerida.'); return; }
    this.guardandoManual.set(true);
    this.error.set('');

    const datos: any = { fecha: this.formManual.fecha };
    const num = (x: string) => x !== '' && x !== null ? parseFloat(x) : undefined;
    const map: Record<string, string> = {
      precipitacion_mm: this.formManual.precipitacion_mm,
      temperatura_max_c: this.formManual.temperatura_max_c,
      temperatura_min_c: this.formManual.temperatura_min_c,
      humedad_relativa_porcentaje: this.formManual.humedad_relativa_porcentaje,
      evapotranspiracion_mm: this.formManual.evapotranspiracion_mm,
    };
    for (const k of Object.keys(map)) {
      const v = num(map[k]);
      if (v !== undefined && !isNaN(v)) datos[k] = v;
    }

    this.svc.registrarEventoManual(this.parcelaId(), datos).subscribe({
      next: () => {
        this.guardandoManual.set(false);
        this.formManual = {
          fecha: '', precipitacion_mm: '', temperatura_max_c: '',
          temperatura_min_c: '', humedad_relativa_porcentaje: '', evapotranspiracion_mm: '',
        };
        this.mostrarFormManual.set(false);
        this.cargarDatos();
      },
      error: (err) => {
        this.guardandoManual.set(false);
        this.error.set(err.error?.error || 'Error al registrar el dato.');
      },
    });
  }

  // ================================================================
  // Semáforos / helpers de presentación
  // ================================================================
  claseUrgencia(u: string): string {
    const v = (u || '').toLowerCase();
    if (v === 'alta' || v === 'critica') return 'rojo';
    if (v === 'media' || v === 'baja') return 'naranja';
    return 'verde';
  }

  claseHumedad(clasif: string): string {
    const v = (clasif || '').toLowerCase();
    if (v === 'critica') return 'rojo';
    if (v === 'baja') return 'naranja';
    if (v === 'moderada') return 'naranja';
    return 'verde';
  }

  claseKs(ks: number | null | undefined): string {
    if (ks == null) return 'gris';
    if (ks >= 0.95) return 'verde';
    if (ks >= 0.75) return 'naranja';
    if (ks >= 0.50) return 'naranja';
    return 'rojo';
  }

  // Porcentaje de llenado del medidor Ks (0..1 → 0..100)
  ksPorcentaje(ks: number | null | undefined): number {
    if (ks == null) return 0;
    return Math.max(0, Math.min(100, ks * 100));
  }

  etiquetaEstres(nivel: string): string {
    const map: Record<string, string> = {
      sin_estres: 'Sin estrés',
      estres_leve: 'Estrés leve',
      estres_moderado: 'Estrés moderado',
      estres_severo: 'Estrés severo',
    };
    return map[nivel] || nivel || '—';
  }

  etiquetaFenologia(e: string): string {
    const map: Record<string, string> = {
      pre_siembra: 'Pre-siembra',
      emergencia: 'Emergencia',
      crecimiento_vegetativo: 'Crecimiento vegetativo',
      floracion: 'Floración',
      llenado_grano: 'Llenado de grano',
      maduracion: 'Maduración',
      cosecha: 'Cosecha',
    };
    return map[e] || e || '—';
  }
}
