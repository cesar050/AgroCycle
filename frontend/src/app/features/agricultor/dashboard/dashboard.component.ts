import {
  Component, ElementRef, OnDestroy,
  computed, effect, inject, signal, viewChild
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { rxResource } from '@angular/core/rxjs-interop';
import { catchError, of } from 'rxjs';
import * as L from 'leaflet';
import { ApiService } from '../../../core/services/api.service';
import { FincaContextService } from '../../../core/services/finca-context.service';
import { MapaService } from '../mapa/services/mapa.service';
import { colorPendiente, colorHumedad, colorElevacion } from '../mapa/mapa.utils';

export type CapaDashboard = 'humedad' | 'pendiente' | 'elevacion';

const ETAPA_LABELS: Record<string, string> = {
  pre_siembra: 'Pre-siembra',
  emergencia: 'Emergencia',
  crecimiento_vegetativo: 'Crecimiento vegetativo',
  floracion: 'Floración',
  llenado_grano: 'Llenado de grano',
  maduracion: 'Maduración',
  cosecha: 'Cosecha',
  post_cosecha: 'Post-cosecha',
};

const NIVEL_ESTRES_LABELS: Record<string, string> = {
  sin_estres: 'Óptimo',
  estres_leve: 'Déficit leve',
  estres_moderado: 'Déficit moderado',
  estres_severo: 'Déficit severo',
};

// Paleta por etapa fenológica para los polígonos del mapa Leaflet —
// misma paleta que usa el SVG de app-mapa-finca, para mantener
// consistencia visual entre el mapa del dashboard y el mapa completo.
const COLORES_ETAPA: Record<string, { fill: string; border: string }> = {
  pre_siembra:            { fill: '#5E3B1E', border: '#3E2510' },
  emergencia:             { fill: '#7FBF3F', border: '#5A8C2A' },
  crecimiento_vegetativo: { fill: '#4E9F3D', border: '#357029' },
  floracion:              { fill: '#2E7D32', border: '#1B5E20' },
  llenado_grano:          { fill: '#E8C547', border: '#B8962A' },
  maduracion:             { fill: '#D4A017', border: '#A07A10' },
  cosecha:                { fill: '#D4A017', border: '#A07A10' },
};

// Color del badge "Etapa actual" de la card de Estado del cultivo.
// Paleta pedida explícitamente (5 etapas clave); el resto de estados
// del backend se completan con un gris neutro.
const ETAPA_COLOR_BADGE: Record<string, string> = {
  pre_siembra: '#9E9E9E',
  emergencia: '#81C784',
  crecimiento_vegetativo: '#388E3C',
  floracion: '#F9A825',
  llenado_grano: '#EF6C00',
  maduracion: '#EF6C00',
  cosecha: '#C62828',
  post_cosecha: '#9E9E9E',
};

function hoyISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function mananaISO(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

function haceDiasISO(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() - dias);
  return d.toISOString().slice(0, 10);
}

interface ItemHoy {
  parcela: string;
  situacion: 'alerta' | 'ok' | 'info';
  situacionTexto: string;
  recomendacion: string;
  prioridad: 'Alta' | 'Normal' | 'Baja';
  fecha: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, DecimalPipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnDestroy {

  private api = inject(ApiService);
  private mapaService = inject(MapaService);
  fincaContext = inject(FincaContextService);

  // ------------------------------------------------------------------
  // Capa temática activa sobre el mapa (Humedad / Pendientes / Elevación)
  // — selección única, excluyente. "Acequias" queda deshabilitada en la
  // UI: no existe aún un endpoint de drenaje georreferenciado (Ks_exceso
  // por parcela); solo existe el campo cualitativo `drenaje` de registro
  // de parcela, que el endpoint /fincas/{id}/mapa ni siquiera devuelve.
  // ------------------------------------------------------------------
  capaActiva = signal<CapaDashboard | null>(null);

  toggleCapa(key: CapaDashboard): void {
    this.capaActiva.update(v => (v === key ? null : key));
  }

  // ------------------------------------------------------------------
  // Mapa Leaflet — fondo satelital ESRI + polígonos de lotes/parcelas
  // ------------------------------------------------------------------
  mapaElRef = viewChild<ElementRef<HTMLDivElement>>('mapaElRef');
  private leafletMap: L.Map | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private observandoResize = false;
  private vistaLista = signal(false);

  constructor() {
    // mapaElRef() es un signal reactivo: el div con #mapaElRef no existe
    // en el DOM mientras cargandoFinca()/tieneTemporada() mantienen
    // activo el bloque @if de carga/onboarding. Este effect se vuelve
    // a ejecutar en cuanto el elemento aparece (o desaparece) en el DOM,
    // a diferencia de afterNextRender (que solo corre una vez y, si el
    // elemento aún no existía, se perdía la inicialización del mapa).
    effect(() => {
      const el = this.mapaElRef()?.nativeElement;

      if (!el) {
        this.resizeObserver?.disconnect();
        this.resizeObserver = null;
        this.observandoResize = false;
        return;
      }
      if (this.observandoResize) return;
      this.observandoResize = true;

      // Espera a que el contenedor tenga una altura real (> 0) antes de
      // marcar la vista como lista — recién ahí Leaflet puede calcular
      // correctamente la grilla de tiles e invalidar su tamaño.
      this.resizeObserver = new ResizeObserver(entries => {
        const h = entries[0]?.contentRect.height ?? 0;
        if (h > 0) {
          this.vistaLista.set(true);
          setTimeout(() => this.leafletMap?.invalidateSize(), 100);
        }
      });
      this.resizeObserver.observe(el);
    });

    // Al cambiar de finca (o llegar sus datos geográficos) se destruye
    // y recrea el mapa por completo — más simple y robusto que mutar
    // las capas de una instancia existente.
    effect(() => {
      if (!this.vistaLista()) return;
      const datos = this.mapaResource.value();
      void this.fincaActiva();
      void this.capaActiva();
      void this.humedadPorParcela();
      this.renderizarMapa(datos);
    });
  }

  ngOnDestroy() {
    this.resizeObserver?.disconnect();
    this.leafletMap?.remove();
  }

  private aLatLngs(coords: number[][]): L.LatLngExpression[] {
    return coords.map(c => [c[1], c[0]] as L.LatLngExpression);
  }

  private renderizarMapa(datos: any) {
    const el = this.mapaElRef()?.nativeElement;
    if (!el) return;

    this.leafletMap?.remove();

    const map = L.map(el, {
      zoomControl: false,
      attributionControl: false,
      dragging: true,
      scrollWheelZoom: true,
      doubleClickZoom: false,
      maxZoom: 17,
      minZoom: 12,
    });

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 17, maxNativeZoom: 17 }
    ).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const finca = datos?.finca;
    const todosLatLngs: L.LatLngExpression[] = [];

    if (finca?.geojson?.coordinates?.[0]) {
      const latlngs = this.aLatLngs(finca.geojson.coordinates[0]);
      L.polygon(latlngs, {
        color: '#FFFFFF', weight: 2.5, opacity: 0.9, fillOpacity: 0, dashArray: '6, 4',
      }).addTo(map);
      todosLatLngs.push(...latlngs);
    }

    (finca?.lotes || []).forEach((lote: any) => {
      if (lote.geojson?.coordinates?.[0]) {
        const latlngs = this.aLatLngs(lote.geojson.coordinates[0]);
        L.polygon(latlngs, {
          color: '#1976D2', weight: 1.5, fillOpacity: 0, dashArray: '5,3',
        }).addTo(map);
        todosLatLngs.push(...latlngs);
      }

      (lote.parcelas || []).forEach((parcela: any) => {
        if (!parcela.geojson?.coordinates?.[0]) return;
        const latlngs = this.aLatLngs(parcela.geojson.coordinates[0]);
        L.polygon(latlngs, {
          color: '#FFFFFF', weight: 1.5, fillColor: this.colorParcela(parcela), fillOpacity: 0.85,
        }).addTo(map);
        todosLatLngs.push(...latlngs);
      });
    });

    if (todosLatLngs.length) {
      map.fitBounds(L.latLngBounds(todosLatLngs), { padding: [20, 20] });
    } else {
      map.setView([-1.83, -78.18], 7); // Ecuador — sin geometría aún
    }

    this.leafletMap = map;
    setTimeout(() => map.invalidateSize(), 100);
  }

  // Color de relleno de cada parcela según la capa temática activa.
  // 'pendiente' y 'elevación' se derivan de campos que ya trae el propio
  // payload de /fincas/{id}/mapa (pendiente, altitud_msnm) — no requieren
  // una petición adicional. 'humedad' sí necesita /mapa/humedad.
  private colorParcela(parcela: any): string {
    const modo = this.capaActiva();

    if (modo === 'pendiente') return colorPendiente(parcela.pendiente ?? 0);

    if (modo === 'elevacion') {
      return colorElevacion(this.normalizarAltitud(parcela.altitud_msnm));
    }

    if (modo === 'humedad') {
      const h = this.humedadPorParcela().get(parcela.id);
      return h ? colorHumedad(h.normalizado) : '#CBD5E1';
    }

    const col = COLORES_ETAPA[parcela.estado_fenologico] || COLORES_ETAPA['pre_siembra'];
    return col.fill;
  }

  private normalizarAltitud(alt: number): number {
    const valores = this.parcelasTerreno()
      .map((p: any) => p.altitud_msnm)
      .filter((v: any) => v != null);
    if (!valores.length) return 0.5;
    const min = Math.min(...valores);
    const max = Math.max(...valores);
    if (max === min) return 0.5;
    return (alt - min) / (max - min);
  }

  // ------------------------------------------------------------------
  // Finca activa (viene del selector global del sidebar)
  // ------------------------------------------------------------------
  fincaActiva = computed(() => this.fincaContext.fincaActiva());

  // ------------------------------------------------------------------
  // Temporada activa de la finca seleccionada
  // ------------------------------------------------------------------
  temporadasResource = rxResource({
    params: () => (this.fincaContext.cargando() ? undefined : true),
    stream: () => this.api.get<any>('/temporadas/historial'),
  });

  temporadaActiva = computed(() => {
    const finca = this.fincaActiva();
    const data = this.temporadasResource.value();
    if (!finca || !data?.temporadas) return null;
    return data.temporadas.find(
      (t: any) => t.estado === 'activa' && t.finca === finca.nombre
    ) ?? null;
  });

  // ------------------------------------------------------------------
  // Detalle de temporada → parcela principal
  // ------------------------------------------------------------------
  temporadaDetalleResource = rxResource({
    params: () => this.temporadaActiva()?.id,
    stream: ({ params }) => this.api.get<any>(`/temporadas/${params}`),
  });

  parcelaPrincipal = computed(
    () => this.temporadaDetalleResource.value()?.parcelas?.[0] ?? null
  );

  // ------------------------------------------------------------------
  // Terreno (parcelas georreferenciadas de la finca)
  // ------------------------------------------------------------------
  parcelasGeojsonResource = rxResource({
    params: () => this.fincaActiva()?.id,
    stream: ({ params }) => this.api.get<any>(`/fincas/${params}/parcelas/geojson`),
  });

  parcelasTerreno = computed(() => this.parcelasGeojsonResource.value()?.parcelas ?? []);

  superficieCultivable = computed(() => {
    const arr = this.parcelasTerreno();
    if (!arr.length) return null;
    return arr.reduce((s: number, p: any) => s + (p.superficie_ha || 0), 0);
  });

  superficieTotal = computed(() => this.fincaActiva()?.superficie_ha ?? this.superficieCultivable());
  altitudPromedio = computed(() => this._promedio('altitud_msnm'));
  pendientePromedio = computed(() => this._promedio('pendiente'));

  private _promedio(campo: string): number | null {
    const valores = this.parcelasTerreno()
      .map((p: any) => p[campo])
      .filter((v: any) => v !== null && v !== undefined);
    if (!valores.length) return null;
    return valores.reduce((s: number, v: number) => s + v, 0) / valores.length;
  }

  mapaResource = rxResource({
    params: () => this.fincaActiva()?.id,
    stream: ({ params }) => this.api.get<any>(`/fincas/${params}/mapa`),
  });

  // Carga diferida: solo se pide al backend cuando la capa "Humedad" está
  // activa, igual que el patrón ya usado en MapaComponent (mapa.component.ts).
  humedadResource = rxResource({
    params: () => (this.capaActiva() === 'humedad' ? this.fincaActiva()?.id : undefined),
    stream: ({ params }) => this.mapaService.obtenerHumedadFinca(params),
  });

  humedadPorParcela = computed(() => {
    const mapa = new Map<string, any>();
    (this.humedadResource.value()?.parcelas ?? []).forEach((h: any) => mapa.set(h.parcela_id, h));
    return mapa;
  });

  leyendaActiva = computed(() => {
    const modo = this.capaActiva();
    if (modo === 'pendiente') {
      return [
        { label: 'Plana', color: '#4CAF50' },
        { label: 'Suave', color: '#CDDC39' },
        { label: 'Moderada', color: '#FFC107' },
        { label: 'Fuerte', color: '#FF5722' },
        { label: 'Escarpada', color: '#B71C1C' },
      ];
    }
    if (modo === 'humedad') {
      return [
        { label: 'Muy baja', color: '#D32F2F' },
        { label: 'Baja', color: '#FF8F00' },
        { label: 'Media', color: '#FDD835' },
        { label: 'Buena', color: '#66BB6A' },
        { label: 'Alta', color: '#1565C0' },
      ];
    }
    if (modo === 'elevacion') {
      return [
        { label: 'Mínima', color: '#2166AC' },
        { label: 'Media', color: '#FEE08B' },
        { label: 'Máxima', color: '#A50026' },
      ];
    }
    return this.leyendaMapa();
  });

  // ------------------------------------------------------------------
  // Leyenda del mapa — etapas presentes en la finca activa
  // ------------------------------------------------------------------
  leyendaMapa = computed(() => {
    const vistos = new Set<string>();
    const out: { etapa: string; label: string; color: string }[] = [];
    this.parcelasTerreno().forEach((p: any) => {
      const etapa = p.estado_fenologico || 'pre_siembra';
      if (vistos.has(etapa)) return;
      vistos.add(etapa);
      out.push({
        etapa,
        label: this.etapaLabel(etapa),
        color: (COLORES_ETAPA[etapa] || COLORES_ETAPA['pre_siembra']).fill,
      });
    });
    return out;
  });

  // ------------------------------------------------------------------
  // Clima — último registro disponible
  // ------------------------------------------------------------------
  climaResource = rxResource({
    params: () => {
      const parcela = this.parcelaPrincipal();
      const inicio = this.temporadaActiva()?.fechas?.inicio;
      if (!parcela?.parcela_id || !inicio) return undefined;
      return { parcelaId: parcela.parcela_id, inicio };
    },
    stream: ({ params }) => this.api.get<any>(
      `/climatico/parcelas/${params.parcelaId}/clima`,
      { fecha_inicio: params.inicio, fecha_fin: hoyISO() }
    ),
  });

  climaDatos = computed(() => this.climaResource.value()?.datos ?? []);

  climaHoy = computed(() => {
    const arr = this.climaDatos();
    return arr.length ? arr[arr.length - 1] : null;
  });

  condicionClima = computed<'lluvia' | 'sol' | null>(() => {
    const hoy = this.climaHoy();
    if (!hoy) return null;
    return (hoy.precipitacion_mm ?? 0) > 0 ? 'lluvia' : 'sol';
  });

  lluviaUltimos7 = computed(() => {
    const corte = haceDiasISO(7);
    const arr = this.climaDatos().filter((d: any) => d.fecha >= corte);
    if (!arr.length) return null;
    return arr.reduce((s: number, d: any) => s + (d.precipitacion_mm || 0), 0);
  });

  // ------------------------------------------------------------------
  // Agua que necesita el cultivo — Ks real vía FAO-56 (CU-CLI-007)
  // ------------------------------------------------------------------
  estresHidricoResource = rxResource({
    params: () => {
      const parcela = this.parcelaPrincipal();
      if (!parcela?.id || !parcela?.parcela_id) return undefined;
      return { tpId: parcela.id, parcelaId: parcela.parcela_id };
    },
    stream: ({ params }) => this.api.post<any>(
      `/climatico/temporada-parcelas/${params.tpId}/estres-hidrico`,
      { parcela_id: params.parcelaId, fecha_inicio: haceDiasISO(7), fecha_fin: hoyISO() }
    ).pipe(
      // El backend responde 404 cuando aun no hay datos climaticos
      // descargados para el periodo (estado vacio legitimo, no un
      // error) — sin este catch, rxResource queda en estado 'error'
      // y cualquier lectura de .value() lanza ResourceValueError.
      catchError(() => of({ datos: [], ks_promedio: null, impacto_rendimiento_porcentaje: null })),
    ),
  });

  estresDatos = computed(() => this.estresHidricoResource.value()?.datos ?? []);

  aguaNecesaria7d = computed(() => {
    const arr = this.estresDatos();
    if (!arr.length) return null;
    return arr.reduce((s: number, d: any) => s + (d.etc_mm || 0), 0);
  });

  nivelEstresActual = computed(() => {
    const arr = this.estresDatos();
    return arr.length ? arr[arr.length - 1].nivel_estres : null;
  });

  et0Promedio = computed(() => {
    const arr = this.estresDatos();
    if (!arr.length) return null;
    const vals = arr.map((d: any) => d.et0_mm).filter((v: any) => v != null);
    if (!vals.length) return null;
    return vals.reduce((s: number, v: number) => s + v, 0) / vals.length;
  });

  etcTotal = computed(() => this.aguaNecesaria7d());
  ksPromedio = computed(() => this.estresHidricoResource.value()?.ks_promedio ?? null);
  impactoRendimiento = computed(() => this.estresHidricoResource.value()?.impacto_rendimiento_porcentaje ?? null);

  aguaPorcentaje = computed(() => {
    const recibida = this.lluviaUltimos7();
    const requerida = this.aguaNecesaria7d();
    if (recibida == null || requerida == null || requerida === 0) return null;
    return Math.min(100, Math.round((recibida / requerida) * 100));
  });

  aguaBarraColor = computed<'verde' | 'amarillo' | 'rojo' | 'gris'>(() => {
    const pct = this.aguaPorcentaje();
    if (pct == null) return 'gris';
    if (pct >= 80) return 'verde';
    if (pct >= 50) return 'amarillo';
    return 'rojo';
  });

  aguaBadgeEstado = computed<'Óptimo' | 'Déficit leve' | 'Déficit severo' | 'Sin datos'>(() => {
    const nivel = this.nivelEstresActual();
    if (!nivel) return 'Sin datos';
    if (nivel === 'sin_estres') return 'Óptimo';
    if (nivel === 'estres_severo') return 'Déficit severo';
    return 'Déficit leve';
  });

  aguaMensaje = computed(() => {
    const nivel = this.nivelEstresActual();
    return nivel && nivel !== 'sin_estres'
      ? 'Tu cultivo podría necesitar más agua.'
      : 'El balance hídrico está en buen estado.';
  });

  // ------------------------------------------------------------------
  // Producción esperada (FAO-33)
  // ------------------------------------------------------------------
  estimacionResource = rxResource({
    params: () => this.temporadaActiva()?.id,
    stream: ({ params }) => this.api.get<any>(`/estimacion/temporada/${params}/estimaciones`),
  });

  estimacionParcelas = computed(() => this.estimacionResource.value()?.parcelas ?? []);
  tieneEstimacion = computed(() => this.estimacionParcelas().length > 0);
  produccionTotalQQ = computed(() => this.estimacionResource.value()?.produccion_total_estimada_qq ?? null);

  rendimientoQqHa = computed(() => {
    const arr = this.estimacionParcelas();
    if (!arr.length) return null;
    const suma = arr.reduce((s: number, p: any) => s + (p.valor_qq_ha || 0), 0);
    return Math.round((suma / arr.length) * 100) / 100;
  });

  margenError = computed(() => this.estimacionParcelas()[0]?.margen_error_porcentaje ?? null);

  // ------------------------------------------------------------------
  // Qué hacer hoy — alertas (prioridad) + actividades, máx 5 en total
  // ------------------------------------------------------------------
  actividadesResource = rxResource({
    params: () => this.temporadaActiva()?.id,
    stream: ({ params }) => this.api.get<any>(`/actividades/temporadas/${params}/actividades`),
  });

  alertasResource = rxResource({
    params: () => (this.fincaActiva() ? true : undefined),
    stream: () => this.api.get<any>('/climatico/alertas'),
  });

  porHacerHoy = computed<ItemHoy[]>(() => {
    const peso: Record<string, number> = { critica: 0, baja: 1 };
    const alertas: ItemHoy[] = [...(this.alertasResource.value()?.alertas ?? [])]
      .sort((a: any, b: any) => (peso[a.clasificacion] ?? 2) - (peso[b.clasificacion] ?? 2))
      .map((a: any) => ({
        parcela: a.parcela_nombre || 'Finca',
        situacion: a.clasificacion === 'critica' ? 'alerta' : 'info',
        situacionTexto: a.clasificacion === 'critica' ? 'Requiere atención' : 'Informativo',
        recomendacion: a.mensaje,
        prioridad: a.clasificacion === 'critica' ? 'Alta' : 'Baja',
        fecha: 'Hoy',
      }));

    const actividades: ItemHoy[] = (this.actividadesResource.value()?.actividades ?? [])
      .map((a: any) => ({
        parcela: a.parcela_nombre || 'General',
        situacion: 'ok',
        situacionTexto: 'Programada',
        recomendacion: a.tipo || 'Actividad',
        prioridad: 'Normal',
        fecha: this.fechaCorta(a.fecha),
      }));

    return [...alertas, ...actividades].slice(0, 5);
  });

  // Sub-bloque "Qué hacer hoy" del Inicio: máximo 3 filas visibles sin
  // scroll; el listado completo vive en /app/actividades.
  porHacerHoyTop3 = computed(() => this.porHacerHoy().slice(0, 3));

  private fechaCorta(iso: string | null | undefined): string {
    if (!iso) return '—';
    if (iso === hoyISO()) return 'Hoy';
    if (iso === mananaISO()) return 'Mañana';
    return new Date(iso).toLocaleDateString('es-EC', { day: 'numeric', month: 'short' });
  }

  // ------------------------------------------------------------------
  // Cosecha estimada — derivada de dias_desde_siembra / avance_ciclo_porcentaje
  // ------------------------------------------------------------------
  diasRestantesCosecha = computed(() => {
    const p = this.parcelaPrincipal();
    if (!p?.dias_desde_siembra || !p?.avance_ciclo_porcentaje) return null;
    const cicloTotal = p.dias_desde_siembra / (p.avance_ciclo_porcentaje / 100);
    return Math.max(0, Math.round(cicloTotal - p.dias_desde_siembra));
  });

  fechaEstimadaCosecha = computed(() => {
    const dias = this.diasRestantesCosecha();
    if (dias == null) return null;
    const d = new Date();
    d.setDate(d.getDate() + dias);
    return d.toISOString().slice(0, 10);
  });

  // Texto plano para el sub-bloque "Estado del cultivo" del Inicio.
  estadoCosechaLabel = computed(() => {
    const p = this.parcelaPrincipal();
    if (!p) return '—';
    if (p.estado_fenologico === 'cosecha') return 'En cosecha';
    if ((p.avance_ciclo_porcentaje ?? 0) >= 100) return 'Cosecha completada';
    const dias = this.diasRestantesCosecha();
    return dias != null ? `Estimada en ${dias} días` : '—';
  });

  // ------------------------------------------------------------------
  // Estados de carga / onboarding
  // ------------------------------------------------------------------
  cargandoFinca = computed(() => this.fincaContext.cargando());
  tieneFinca = computed(() => this.fincaContext.fincas().length > 0);
  cargandoTemporada = computed(() => this.temporadasResource.isLoading());
  tieneTemporada = computed(() => !!this.temporadaActiva());

  etapaLabel(etapa: string | null | undefined): string {
    if (!etapa) return '—';
    return ETAPA_LABELS[etapa] ?? etapa;
  }

  nivelEstresLabel(nivel: string | null | undefined): string {
    if (!nivel) return '—';
    return NIVEL_ESTRES_LABELS[nivel] ?? '—';
  }

  estadoGeneralLabel(nivel: string | null | undefined): 'Bien' | 'Atención' | 'En riesgo' | 'Sin datos' {
    if (!nivel) return 'Sin datos';
    if (nivel === 'sin_estres' || nivel === 'estres_leve') return 'Bien';
    if (nivel === 'estres_moderado') return 'Atención';
    return 'En riesgo';
  }

  colorEtapaBadge(etapa: string | null | undefined): string {
    if (!etapa) return ETAPA_COLOR_BADGE['pre_siembra'];
    return ETAPA_COLOR_BADGE[etapa] ?? ETAPA_COLOR_BADGE['pre_siembra'];
  }

  abrirSelectorFinca() {
    this.fincaContext.selectorAbierto.set(true);
  }
}
