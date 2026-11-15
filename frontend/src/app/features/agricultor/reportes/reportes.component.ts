import {
  Component, OnInit, signal, computed, effect,
  viewChild, ElementRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import {
  Chart, ScatterController, LineController,
  PointElement, LineElement, LinearScale, Tooltip, Legend,
} from 'chart.js';

// Registro mínimo (tree-shaking) de los controladores que usa el scatter.
Chart.register(
  ScatterController, LineController,
  PointElement, LineElement, LinearScale, Tooltip, Legend,
);

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.scss',
})
export class ReportesComponent implements OnInit {

  // Paleta fija de alto contraste (coherente con la estética SIG del
  // dashboard; validada CVD con la skill dataviz).
  private readonly COL_PUNTO  = '#2563EB'; // azul — parcelas (datos)
  private readonly COL_TREND  = '#16A34A'; // verde — línea de tendencia
  private readonly COL_IDENT  = '#94A3B8'; // gris  — predicción perfecta y=x
  private readonly COL_TEXT   = '#0F172A';
  private readonly COL_SEC    = '#64748B';
  private readonly COL_GRID   = '#E2E8F0';
  private readonly COL_SURF   = '#FFFFFF';

  // --- Estado general ---
  cargando    = signal(true);
  descargando = signal<string | null>(null);
  error       = signal('');

  temporadas  = signal<any[]>([]);
  temporadaId = signal('');
  tpId        = signal('');

  // --- CU-EST-006 (validación científica, global) ---
  comparacion   = signal<any | null>(null);
  cargandoComp  = signal(true);

  // --- CU-REP-004 (dashboard de la temporada seleccionada) ---
  dashboard     = signal<any | null>(null);
  cargandoDash  = signal(false);

  // --- CU-REP-005 (comparativo entre temporadas) ---
  comparativo   = signal<any | null>(null);
  cargandoComparativo = signal(true);

  // --- Derivados de la validación ---
  suficiente = computed(() => !!this.comparacion()?.suficiente);
  puntos     = computed<any[]>(() => this.comparacion()?.puntos ?? []);
  metricas   = computed(() => this.comparacion()?.metricas ?? null);
  alerta     = computed(() => this.comparacion()?.alerta ?? null);

  private scatterCanvas = viewChild<ElementRef<HTMLCanvasElement>>('scatter');
  private chart?: Chart;

  constructor(private api: ApiService) {
    // Reconstruye el scatter cuando cambian los datos o aparece el canvas.
    effect(() => {
      const canvas = this.scatterCanvas();
      const pts = this.puntos();
      if (this.suficiente() && canvas && pts.length >= 2) {
        this.render(canvas.nativeElement, pts);
      } else if (this.chart) {
        this.chart.destroy();
        this.chart = undefined;
      }
    });
  }

  ngOnInit() {
    this.cargarValidacionGlobal();
    this.cargarComparativo();
    this.cargarTemporadas();
  }

  // ---------------------------------------------------------------
  // Carga de datos
  // ---------------------------------------------------------------
  cargarValidacionGlobal() {
    this.cargandoComp.set(true);
    this.api.get<any>('/estimacion/comparacion-real').subscribe({
      next: (res) => { this.comparacion.set(res); this.cargandoComp.set(false); },
      error: () => this.cargandoComp.set(false),
    });
  }

  cargarComparativo() {
    this.cargandoComparativo.set(true);
    this.api.get<any>('/reportes/dashboard-comparativo').subscribe({
      next: (res) => { this.comparativo.set(res); this.cargandoComparativo.set(false); },
      error: () => this.cargandoComparativo.set(false),
    });
  }

  cargarTemporadas() {
    this.api.get<any>('/temporadas/historial').subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa') || lista[0];
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarDashboard(activa.id);
          this.cargarTpId(activa.id);
        }
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarDashboard(temporadaId: string) {
    this.cargandoDash.set(true);
    this.dashboard.set(null);
    this.api.get<any>(`/reportes/temporadas/${temporadaId}/dashboard`).subscribe({
      next: (res) => { this.dashboard.set(res); this.cargandoDash.set(false); },
      error: () => this.cargandoDash.set(false),
    });
  }

  // El tp_id para la ficha PDF se toma del detalle de la temporada,
  // que lista sus parcelas vinculadas (parcelas[].id === temporada_parcela_id).
  cargarTpId(temporadaId: string) {
    this.api.get<any>(`/temporadas/${temporadaId}`).subscribe({
      next: (res) => {
        const primera = res.parcelas?.[0];
        this.tpId.set(primera?.id || '');
      },
      error: () => this.tpId.set(''),
    });
  }

  cambiarTemporada(id: string) {
    this.temporadaId.set(id);
    this.tpId.set('');
    this.cargarDashboard(id);
    this.cargarTpId(id);
  }

  // ---------------------------------------------------------------
  // Descarga de ficha técnica PDF — vía infraestructura HTTP del proyecto
  // (ApiService.getBlob + environment.apiUrl). Sin fetch nativo,
  // sin URL hardcodeada, sin leer el token de localStorage.
  // ---------------------------------------------------------------
  descargarFicha() {
    if (!this.tpId()) {
      this.error.set('No hay parcela vinculada a esta temporada.');
      return;
    }
    this.descargando.set('ficha');
    this.error.set('');

    this.api.getBlob(`/reportes/temporada-parcela/${this.tpId()}/ficha-tecnica`)
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download =
            `ficha-tecnica-${this.temporadaActual?.nombre || 'temporada'}.pdf`;
          link.click();
          URL.revokeObjectURL(url);
          this.descargando.set(null);
        },
        error: () => {
          this.descargando.set(null);
          this.error.set('Error al generar el PDF. Intenta de nuevo.');
        },
      });
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }

  // ---------------------------------------------------------------
  // Scatter: Estimado (x) vs Real (y) + línea de tendencia + y=x
  // ---------------------------------------------------------------
  private render(canvas: HTMLCanvasElement, pts: any[]) {
    if (this.chart) { this.chart.destroy(); }

    const xs = pts.map(p => p.estimado_qq);
    const ys = pts.map(p => p.real_qq);
    const n = pts.length;

    // Regresión por mínimos cuadrados (y = a + b·x).
    const mx = xs.reduce((a, b) => a + b, 0) / n;
    const my = ys.reduce((a, b) => a + b, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) {
      num += (xs[i] - mx) * (ys[i] - my);
      den += (xs[i] - mx) ** 2;
    }
    const slope = den === 0 ? 0 : num / den;
    const intercept = my - slope * mx;

    const maxV = Math.max(...xs, ...ys);
    const axisMax = Math.max(Math.ceil(maxV * 1.1), 1);
    const axisMin = 0;

    this.chart = new Chart(canvas, {
      type: 'scatter',
      data: {
        datasets: [
          {
            type: 'line',
            label: 'Predicción perfecta (y = x)',
            data: [{ x: axisMin, y: axisMin }, { x: axisMax, y: axisMax }],
            borderColor: this.COL_IDENT,
            borderWidth: 1.5,
            borderDash: [5, 4],
            pointRadius: 0,
            fill: false,
            order: 3,
          },
          {
            type: 'line',
            label: 'Línea de tendencia (ajuste lineal)',
            data: [
              { x: axisMin, y: intercept + slope * axisMin },
              { x: axisMax, y: intercept + slope * axisMax },
            ],
            borderColor: this.COL_TREND,
            borderWidth: 2,
            pointRadius: 0,
            fill: false,
            order: 2,
          },
          {
            type: 'scatter',
            label: 'Parcela cosechada',
            data: pts.map(p => ({
              x: p.estimado_qq, y: p.real_qq,
              parcela: p.parcela_nombre, temporada: p.temporada_nombre,
              err: p.error_pct,
            })) as any,
            backgroundColor: this.COL_PUNTO,
            borderColor: this.COL_SURF,
            borderWidth: 2,       // anillo de superficie (dataviz)
            pointRadius: 6,
            pointHoverRadius: 8,
            order: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'point', intersect: true },
        scales: {
          x: {
            type: 'linear', min: axisMin, max: axisMax,
            title: { display: true, text: 'Producción estimada (qq)', color: this.COL_SEC, font: { size: 11 } },
            grid: { color: this.COL_GRID },
            ticks: { color: this.COL_SEC, font: { size: 10 } },
          },
          y: {
            type: 'linear', min: axisMin, max: axisMax,
            title: { display: true, text: 'Producción real (qq)', color: this.COL_SEC, font: { size: 11 } },
            grid: { color: this.COL_GRID },
            ticks: { color: this.COL_SEC, font: { size: 10 } },
          },
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: this.COL_TEXT, boxWidth: 18, boxHeight: 2,
              usePointStyle: false, font: { size: 10 },
            },
          },
          tooltip: {
            callbacks: {
              label: (ctx: any) => {
                const r = ctx.raw;
                if (r && r.parcela != null) {
                  return [
                    `${r.parcela}${r.temporada ? ' · ' + r.temporada : ''}`,
                    `Estimado: ${r.x} qq`,
                    `Real: ${r.y} qq`,
                    `Error: ${r.err}%`,
                  ];
                }
                return ctx.dataset.label || '';
              },
            },
          },
        },
      },
    });
  }
}
