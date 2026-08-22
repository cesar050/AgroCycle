import {
  Component, OnInit, OnDestroy, signal,
  AfterViewInit, ElementRef, ViewChild, NgZone
} from '@angular/core';
import { CommonModule, DecimalPipe, SlicePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../auth/services/auth.service';
import { MapaFincaComponent } from '../../../shared/components/mapa-finca/mapa-finca.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, DecimalPipe, SlicePipe, MapaFincaComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('mapaRef')    mapaRef!:    ElementRef;
  @ViewChild('graficaRef') graficaRef!: ElementRef;

  cargando        = signal(true);
  tieneFinca      = signal(false);
  tieneTemporada  = signal(false);

  finca           = signal<any>(null);
  temporada       = signal<any>(null);
  estimacion      = signal<any>(null);
  financiero      = signal<any>(null);
  recomendaciones = signal<any[]>([]);
  parcelas        = signal<any[]>([]);
  datosMapa       = signal<any>(null);
  actividades     = signal<any[]>([]);

  private mapa:    any = null;
  private grafica: any = null;
  private mapaListo = false;

  ksEtapas = [
    { key: 'emergencia',  label: 'Emergencia',  done: true,  current: false, ks: 1.000, color: '#2E7D32' },
    { key: 'crecimiento', label: 'Crecimiento', done: true,  current: false, ks: 0.795, color: '#F57C00' },
    { key: 'floracion',   label: 'Floración',   done: true,  current: false, ks: 1.000, color: '#2E7D32' },
    { key: 'llenado',     label: 'Llenado',     done: true,  current: false, ks: 1.000, color: '#2E7D32' },
    { key: 'maduracion',  label: 'Maduración',  done: true,  current: false, ks: 1.000, color: '#2E7D32' },
    { key: 'cosecha',     label: 'Cosecha',     done: false, current: true,  ks: 1.000, color: '#2E7D32' },
  ];

  constructor(
    private api: ApiService,
    public authService: AuthService,
    private zone: NgZone,
  ) {}

  ngOnInit()        { this.cargarDatos(); }
  ngAfterViewInit() {}

  cargarDatos() {
    this.cargando.set(true);
    this.api.get<any>('/fincas').subscribe({
      next: (res) => {
        const fincas = Array.isArray(res) ? res : (res.fincas || []);
        if (fincas.length > 0) {
          this.tieneFinca.set(true);
          this.cargarMapaFinca(fincas[0].id);
          this.finca.set(fincas[0]);
          this.cargarTemporada();
          this.cargarParcelasGeojson(fincas[0].id);
        } else {
          this.tieneFinca.set(false);
          this.cargando.set(false);
        }
      },
      error: () => { this.tieneFinca.set(false); this.cargando.set(false); }
    });
  }

  cargarParcelasGeojson(fincaId: string) {
    this.api.get<any>(`/fincas/${fincaId}/parcelas/geojson`).subscribe({
      next: (res) => {
        this.parcelas.set(res.parcelas || []);
        if (this.mapaListo) this.dibujarParcelas();
      },
      error: () => this.parcelas.set([]),
    });
  }

  cargarTemporada() {
    this.api.get<any>('/temporadas/historial').subscribe({
      next: (res) => {
        const lista  = res.temporadas || [];
        const activa = lista.find((t: any) => t.estado === 'activa');
        if (activa) {
          this.tieneTemporada.set(true);
          this.temporada.set(activa);
          this.cargarFinanciero(activa.id);
          this.cargarEstimacion(activa.id);
          this.cargarRecomendaciones(activa.id);
          this.cargarActividades(activa.id);
        } else {
          this.tieneTemporada.set(false);
          this.cargando.set(false);
        }
      },
      error: () => { this.tieneTemporada.set(false); this.cargando.set(false); }
    });
  }

  cargarFinanciero(id: string) {
    this.api.get<any>(`/financiero/temporadas/${id}/rentabilidad`).subscribe({
      next:  (r) => this.financiero.set(r),
      error: ()  => this.financiero.set(null),
    });
  }

  cargarEstimacion(id: string) {
    this.api.get<any>(`/estimacion/temporada/${id}/estimaciones`).subscribe({
      next: (r) => {
        this.estimacion.set(r);
        this.cargando.set(false);
        setTimeout(() => {
          this.inicializarMapa();
          this.inicializarGrafica();
        }, 200);
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarRecomendaciones(temporadaId: string) {
    this.api.get<any>(
      `/agronomo/temporadas/${temporadaId}/recomendaciones`
    ).subscribe({
      next:  (r) => this.recomendaciones.set(r.recomendaciones || []),
      error: ()  => this.recomendaciones.set([]),
    });
  }

    cargarMapaFinca(fincaId: string) {
    this.api.get<any>(`/fincas/${fincaId}/mapa`).subscribe({
      next:  (r) => this.datosMapa.set(r),
      error: () => this.datosMapa.set(null),
    });
  }

    cargarActividades(temporadaId: string) {
    this.api.get<any>(`/actividades/temporadas/${temporadaId}/actividades`).subscribe({
      next:  (r) => this.actividades.set(r.actividades || []),
      error: ()  => this.actividades.set([]),
    });
  }

  private async inicializarMapa() {
    if (!this.mapaRef?.nativeElement || this.mapa) return;

    const L = await import('leaflet');

    // Fix íconos Leaflet con webpack
    const iconDefault = L.icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize:    [25, 41],
      iconAnchor:  [12, 41],
      popupAnchor: [1, -34],
      shadowSize:  [41, 41],
    });
    L.Marker.prototype.options.icon = iconDefault;

    this.mapa = L.map(this.mapaRef.nativeElement, {
      zoomControl:       true,
      attributionControl: false,
      scrollWheelZoom:   true,
    });

    // Capa satelital ArcGIS
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21, attribution: '' }
    ).addTo(this.mapa);

    // Capa de etiquetas encima del satélite
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21, opacity: 0.7 }
    ).addTo(this.mapa);

    this.mapaListo = true;

    // Si las parcelas ya cargaron, dibujarlas
    if (this.parcelas().length > 0) {
      this.dibujarParcelas();
    } else {
      // Posición por defecto mientras cargan
      this.mapa.setView([-4.0876, -79.8193], 17);
    }
  }

  private dibujarParcelas() {
    if (!this.mapa) return;

    import('leaflet').then(L => {
      const parcelas = this.parcelas();
      const allBounds: any[] = [];

      const colores: Record<string, string> = {
        'cosecha':              '#2E7D32',
        'maduracion':           '#558B2F',
        'llenado_grano':        '#388E3C',
        'floracion':            '#43A047',
        'crecimiento_vegetativo':'#66BB6A',
        'emergencia':           '#81C784',
        'pre_siembra':          '#A5D6A7',
      };

      parcelas.forEach(p => {
        if (!p.geojson || !p.geojson.coordinates) return;

        // Convertir [lng, lat] → [lat, lng] para Leaflet
        const coords = p.geojson.coordinates[0].map(
          (c: number[]) => [c[1], c[0]] as [number, number]
        );

        const etapa  = p.estado_fenologico || 'pre_siembra';
        const color  = colores[etapa] || '#43A047';

        const poligono = L.polygon(coords, {
          color:       '#ffffff',
          weight:      2,
          fillColor:   color,
          fillOpacity: 0.55,
        }).addTo(this.mapa);

        // Popup con info de la parcela
        poligono.bindPopup(`
          <div style="font-family:Inter,sans-serif;font-size:12px;min-width:160px">
            <p style="font-weight:700;font-size:13px;margin-bottom:6px;color:#212529">
              ${p.nombre}
            </p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px">
              <div>
                <p style="color:#6c757d;font-size:10px;margin-bottom:1px">Superficie</p>
                <p style="font-weight:600">${p.superficie_ha} ha</p>
              </div>
              <div>
                <p style="color:#6c757d;font-size:10px;margin-bottom:1px">Altitud</p>
                <p style="font-weight:600">${p.altitud_msnm} msnm</p>
              </div>
              <div>
                <p style="color:#6c757d;font-size:10px;margin-bottom:1px">Pendiente</p>
                <p style="font-weight:600">${p.pendiente}%</p>
              </div>
              <div>
                <p style="color:#6c757d;font-size:10px;margin-bottom:1px">Etapa</p>
                <p style="font-weight:600;color:${color}">${etapa.replace('_',' ')}</p>
              </div>
            </div>
          </div>
        `, { maxWidth: 220 });

        // Label con nombre de la parcela
        const bounds   = poligono.getBounds();
        const centroide = bounds.getCenter();

        const label = L.divIcon({
          className: '',
          html: `
            <div style="
              background:rgba(0,0,0,0.65);
              color:#fff;
              padding:3px 8px;
              border-radius:4px;
              font-size:11px;
              font-weight:600;
              font-family:Inter,sans-serif;
              white-space:nowrap;
              pointer-events:none;
            ">${p.nombre}</div>
          `,
          iconAnchor: [40, 8],
        });

        L.marker(centroide, { icon: label, interactive: false })
          .addTo(this.mapa);

        allBounds.push(...coords);
      });

      // Ajustar vista a todas las parcelas
      if (allBounds.length > 0) {
        this.mapa.fitBounds(allBounds, { padding: [30, 30] });
      }
    });
  }

  private async inicializarGrafica() {
    if (!this.graficaRef?.nativeElement || this.grafica) return;

    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    const ctx = this.graficaRef.nativeElement.getContext('2d');

    this.grafica = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Emergencia','Crec. Veg.','Floración','Llen. Grano','Maduración','Cosecha'],
        datasets: [{
          label: 'Ks',
          data:  [1.000, 0.795, 1.000, 1.000, 1.000, 1.000],
          backgroundColor: [
            '#2E7D32','#F57C00','#2E7D32',
            '#2E7D32','#2E7D32','#2E7D32',
          ],
          borderRadius:     5,
          borderSkipped:    false,
          maxBarThickness:  36,
        }]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#212529',
            titleFont:   { size: 12, family: 'Inter' },
            bodyFont:    { size: 12, family: 'JetBrains Mono' },
            padding:     10,
            cornerRadius: 6,
            callbacks: {
              title: (items: any[]) => items[0].label,
              label: (c: any)       => ` Ks = ${Number(c.raw).toFixed(3)}`,
            }
          }
        },
        scales: {
          y: {
            min: 0, max: 1.2,
            grid:   { color: 'rgba(0,0,0,0.05)' },
            border: { display: false },
            ticks:  {
              font:      { size: 11, family: 'JetBrains Mono' },
              color:     '#6C757D',
              stepSize:  0.3,
              callback:  (v: any) => v.toFixed(1),
            }
          },
          x: {
            grid:   { display: false },
            border: { display: false },
            ticks:  { font: { size: 11, family: 'Inter' }, color: '#6C757D' }
          }
        }
      }
    });
  }

  ngOnDestroy() {
    this.mapa?.remove();     this.mapa    = null;
    this.grafica?.destroy(); this.grafica = null;
  }

  get nombreCorto(): string {
    const u = this.authService.usuarioActual();
    return u?.nombre?.split(' ')?.[0] || 'Agricultor';
  }

  get gananciaPositiva(): boolean {
    return (this.financiero()?.resultado?.ganancia_neta ?? 0) >= 0;
  }
}