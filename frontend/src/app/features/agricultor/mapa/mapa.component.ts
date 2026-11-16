import {
  Component, OnDestroy, signal, computed, effect, viewChild, ElementRef, inject,
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { Router } from '@angular/router';
import * as L from 'leaflet';

import { MapaService } from './services/mapa.service';
import { LeafletMapaService } from './services/leaflet-mapa.service';
import { MapaStateService, MapaBase, Parcela, Lote } from './services/mapa-state.service';
import { PanelGestionarFincaComponent } from './components/panel-gestionar-finca/panel-gestionar-finca.component';
import { PanelGestionarLoteComponent } from './components/panel-gestionar-lote/panel-gestionar-lote.component';
import { PanelGestionarParcelaComponent } from './components/panel-gestionar-parcela/panel-gestionar-parcela.component';
import { construirGeoJSONParcelas, construirGeoJSONLotes, calcularCentro } from './mapa.utils';
import { ETAPAS_FENOLOGICAS, EtapaFenologicaPipe } from './pipes/etapa-fenologica.pipe';

const TILES_BASE: Record<MapaBase, string> = {
  satelite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  relieve:  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
  claro:    'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
};

const BASES_MAPA: { key: MapaBase; label: string }[] = [
  { key: 'satelite', label: 'Satélite' },
  { key: 'relieve',  label: 'Relieve' },
  { key: 'claro',    label: 'Claro' },
];

// Centro por defecto (zona agrícola de Loja, Ecuador) usado únicamente
// cuando el agricultor todavía no tiene ninguna finca y abre el panel
// "Registrar primera finca": necesita un mapa en blanco sobre el que
// dibujar el primer polígono.
const CENTRO_DEFECTO: [number, number] = [-4.0876, -79.8193];

// Vista general — "Mapa normal". Las capas especializadas (pendiente,
// elevación, humedad FAO-56/FAO-33) viven en sus propias subrutinas
// dedicadas (/app/mapa/topografia, /app/mapa/humedad); aquí solo se
// pinta el estado fenológico, que es el control básico de la finca.
// El panel técnico del 20% también es, mientras `panelMode()` no es
// 'visor', el flujo transaccional de alta/edición/baja de Fincas,
// Lotes y Parcelas (ver components/panel-gestionar-*).
@Component({
  selector: 'app-mapa',
  standalone: true,
  imports: [
    CommonModule, DecimalPipe, EtapaFenologicaPipe,
    PanelGestionarFincaComponent, PanelGestionarLoteComponent, PanelGestionarParcelaComponent,
  ],
  providers: [MapaStateService],
  templateUrl: './mapa.component.html',
  styleUrl: './mapa.component.scss',
})
export class MapaComponent implements OnDestroy {

  state = inject(MapaStateService);

  private mapaService = inject(MapaService);
  private leafletMapaService = inject(LeafletMapaService);
  private router = inject(Router);

  mapaElRef = viewChild<ElementRef>('mapaLeaflet');

  // Única variable de UI: colapsa el panel lateral para que el mapa
  // ocupe el 100% del contenedor, y viceversa.
  pantallaCompleta = signal(false);

  // Acciones inline de la navegación jerárquica (eliminar lote/parcela
  // desde la lista, sin pasar por el panel CRUD completo).
  eliminandoId = signal<string | null>(null);
  errorAccion  = signal<string | null>(null);

  // Expande el bloque de detalle técnico extendido (avance de ciclo,
  // producción real, estimación) de la parcela seleccionada.
  detalleTecnicoAbierto = signal(false);

  basesMapa = BASES_MAPA;

  private capaParcelas: L.Layer | null = null;
  private capaLotes: L.Layer | null = null;

  private readonly coloresEtapas: Record<string, string> = Object.fromEntries(
    ETAPAS_FENOLOGICAS.map(e => [e.key, e.color])
  );

  private readonly titulosPanel: Record<string, string> = {
    'crear-finca': 'Registrar finca',
    'editar-finca': 'Gestionar finca',
    'crear-lote': 'Nuevo lote',
    'editar-lote': 'Gestionar lote',
    'crear-parcela': 'Nueva parcela',
    'editar-parcela': 'Gestionar parcela',
  };

  tituloPanel = computed(() => this.titulosPanel[this.state.panelMode()] ?? '');

  // Panel lateral: 30% en navegación (visor), 40% mientras hay un
  // formulario de Crear/Editar Finca/Lote/Parcela abierto — evita los
  // formularios estrechos e ilegibles del 20% original.
  panelFormularioActivo = computed(() => this.state.panelMode() !== 'visor');

  constructor() {
    // 1) Cargar los datos del mapa cada vez que cambia la finca activa.
    effect(() => {
      const finca = this.state.fincaActiva();
      const cargandoFincas = this.state.cargandoFincas();
      this.state.resetSeleccionFinca();

      if (cargandoFincas) return;

      if (!finca) {
        this.state.datosMapa.set(null);
        this.state.cargando.set(false);
        return;
      }

      this.cargarMapaFinca(finca.id, { marcarCargando: true });
    });

    // 2) Ciclo de vida del mapa Leaflet. Normalmente centra en la
    // finca activa; si todavía no hay ninguna finca pero se abrió el
    // panel "Registrar primera finca", inicializa un mapa en blanco
    // para poder dibujar el primer polígono.
    effect(() => {
      const el = this.mapaElRef()?.nativeElement;
      if (!el) return;

      const datos = this.state.datosMapa();
      const creandoPrimeraFinca = !datos?.finca && this.state.panelMode() === 'crear-finca';
      if (!datos?.finca && !creandoPrimeraFinca) return;

      const centro = datos?.finca ? calcularCentro(datos.finca.geojson) : null;

      this.leafletMapaService.destroy();
      const mapa = this.leafletMapaService.initMap(el.id, centro ?? CENTRO_DEFECTO, 15);

      if (datos?.finca?.geojson) {
        this.leafletMapaService.agregarLimiteFinca(mapa, datos.finca.geojson);
        this.leafletMapaService.fitBounds(mapa, datos.finca.geojson);
      }

      mapa.on('mousemove', (e: L.LeafletMouseEvent) => {
        this.state.cursorLatLng.set({ lat: e.latlng.lat, lng: e.latlng.lng });
      });

      this.state.mapaLeaflet.set(mapa);
    });

    // 3) Mapa base (satélite / relieve / claro).
    effect(() => {
      const base = this.state.mapaBase();
      const mapa = this.state.mapaLeaflet();
      if (!mapa) return;

      mapa.eachLayer(layer => {
        if (layer instanceof L.TileLayer) mapa.removeLayer(layer);
      });
      L.tileLayer(TILES_BASE[base], {
        attribution: 'Esri', maxZoom: 19, maxNativeZoom: 17,
      }).addTo(mapa);
    });

    // 4) Lotes (borde azul, con tooltip nombre + hectáreas). Se dibujan
    // antes que las parcelas para que, al superponerse visualmente, el
    // polígono de una parcela (añadido después, por lo tanto encima en
    // el SVG) capture el clic primero que el de su lote contenedor.
    effect(() => {
      const datos = this.state.datosMapa();
      const mapa  = this.state.mapaLeaflet();
      if (!mapa || !datos?.finca) return;

      if (this.capaLotes) {
        mapa.removeLayer(this.capaLotes);
        this.capaLotes = null;
      }

      const geojsonLotes = construirGeoJSONLotes(datos.finca);
      const capa = this.leafletMapaService.agregarCapaLotes(mapa, geojsonLotes);
      this.engancharSeleccionLote(capa);
      this.capaLotes = capa;
      this.aplicarResaltadoLote();
    });

    // 5) Parcelas coloreadas por etapa fenológica — única capa temática
    // de esta vista general.
    effect(() => {
      const datos = this.state.datosMapa();
      const mapa  = this.state.mapaLeaflet();
      if (!mapa || !datos?.finca) return;

      if (this.capaParcelas) {
        mapa.removeLayer(this.capaParcelas);
        this.capaParcelas = null;
      }

      const geojsonParcelas = construirGeoJSONParcelas(datos.finca);
      const capa = this.leafletMapaService.agregarCapaParcelas(mapa, geojsonParcelas, this.coloresEtapas);
      this.engancharSeleccion(capa);
      this.capaParcelas = capa;
      this.aplicarResaltadoSeleccion();
    });

    // 6) Resaltado de la parcela y el lote seleccionados.
    effect(() => {
      this.state.parcelaSeleccionadaId();
      this.aplicarResaltadoSeleccion();
    });
    effect(() => {
      this.state.loteSeleccionadoId();
      this.aplicarResaltadoLote();
    });

    // 7) Zoom automático: al entrar a un lote (nivel 2 de la
    // navegación) encuadra su polígono; al volver al nivel de finca
    // (ningún lote seleccionado) vuelve a encuadrar la finca completa.
    effect(() => {
      const mapa = this.state.mapaLeaflet();
      const lote = this.state.loteSeleccionado();
      const datos = this.state.datosMapa();
      if (!mapa) return;
      if (lote?.geojson) {
        this.leafletMapaService.fitBounds(mapa, lote.geojson);
      } else if (datos?.finca?.geojson) {
        this.leafletMapaService.fitBounds(mapa, datos.finca.geojson);
      }
    });
  }

  ngOnDestroy(): void {
    this.leafletMapaService.destroy();
  }

  onParcelaElegida(parcela: Parcela): void {
    this.state.seleccionarParcela(parcela.id);
    const mapa = this.state.mapaLeaflet();
    if (!mapa || !parcela?.geojson) return;
    const layer = L.geoJSON(parcela.geojson);
    mapa.fitBounds(layer.getBounds(), { maxZoom: 16 });
  }

  editarParcela(parcela: Parcela, evento: Event): void {
    evento.stopPropagation();
    this.state.parcelaSeleccionadaId.set(parcela.id);
    this.state.panelMode.set('editar-parcela');
  }

  gestionarFinca(): void {
    this.state.panelMode.set(this.state.fincaActiva() ? 'editar-finca' : 'crear-finca');
  }

  reintentarCargaMapa(): void {
    const finca = this.state.fincaActiva();
    if (!finca) return;
    this.cargarMapaFinca(finca.id, { marcarCargando: true });
  }

  elegirBase(base: MapaBase): void {
    this.state.mapaBase.set(base);
  }

  toggleVistaCompleta(): void {
    this.pantallaCompleta.update(v => !v);
    setTimeout(() => this.state.mapaLeaflet()?.invalidateSize(), 220);
  }

  // ================================================================
  // Navegación jerárquica Finca > Lote > Parcela (panel lateral)
  // ================================================================

  nuevoLote(): void {
    this.state.panelMode.set('crear-lote');
  }

  verParcelasDeLote(lote: Lote): void {
    this.state.seleccionarLote(lote.id);
  }

  editarLoteDesdeLista(lote: Lote, evento: Event): void {
    evento.stopPropagation();
    this.state.loteEnContexto.set(lote.id);
    this.state.panelMode.set('editar-lote');
  }

  eliminarLoteDesdeLista(lote: Lote, evento: Event): void {
    evento.stopPropagation();
    if (!confirm(`¿Eliminar el lote "${lote.nombre}"? Esta acción no se puede deshacer.`)) return;

    this.errorAccion.set(null);
    this.eliminandoId.set(lote.id);
    this.mapaService.eliminarLote(lote.id).subscribe({
      next: () => {
        this.eliminandoId.set(null);
        if (this.state.loteSeleccionadoId() === lote.id) this.state.volverALotes();
        this.refrescarMapaSilencioso();
      },
      error: (err) => {
        this.eliminandoId.set(null);
        this.errorAccion.set(err.error?.error || 'No se pudo eliminar el lote.');
      },
    });
  }

  nuevaParcelaEnLote(lote: Lote): void {
    this.state.loteEnContexto.set(lote.id);
    this.state.panelMode.set('crear-parcela');
  }

  eliminarParcelaDesdeLista(parcela: Parcela, evento: Event): void {
    evento.stopPropagation();
    if (!confirm(`¿Eliminar la parcela "${parcela.nombre}"? Esta acción no se puede deshacer.`)) return;

    this.errorAccion.set(null);
    this.eliminandoId.set(parcela.id);
    this.mapaService.eliminarParcela(parcela.id).subscribe({
      next: () => {
        this.eliminandoId.set(null);
        if (this.state.parcelaSeleccionadaId() === parcela.id) this.state.cerrarPanelDerecho();
        this.refrescarMapaSilencioso();
      },
      error: (err) => {
        this.eliminandoId.set(null);
        this.errorAccion.set(err.error?.error || 'No se pudo eliminar la parcela.');
      },
    });
  }

  irARegistrarActividad(parcelaId: string): void {
    this.router.navigate(['/app/actividades/nueva'], { queryParams: { parcela: parcelaId } });
  }

  toggleDetalleTecnico(): void {
    this.detalleTecnicoAbierto.update(v => !v);
  }

  // ================================================================
  // Helpers privados
  // ================================================================

  private cargarMapaFinca(fincaId: string, opts: { marcarCargando?: boolean } = {}): void {
    if (opts.marcarCargando) this.state.cargando.set(true);
    this.mapaService.obtenerMapaFinca(fincaId).subscribe({
      next: (res) => {
        this.state.datosMapa.set(res);
        this.state.errorRefresco.set(null);
        if (opts.marcarCargando) this.state.cargando.set(false);
      },
      error: () => {
        if (opts.marcarCargando) this.state.cargando.set(false);
        this.state.errorRefresco.set(
          'No se pudo actualizar el mapa de esta finca. Verifica tu conexión e intenta de nuevo.'
        );
      },
    });
  }

  // Igual que cargarMapaFinca pero sin tocar el signal `cargando` — se
  // usa tras eliminar un lote/parcela desde la lista, donde ya hay un
  // indicador de carga propio por fila (eliminandoId).
  private refrescarMapaSilencioso(): void {
    const finca = this.state.fincaActiva();
    if (!finca) return;
    this.cargarMapaFinca(finca.id);
  }

  private engancharSeleccion(capa: L.Layer): void {
    if (!(capa instanceof L.GeoJSON)) return;
    capa.eachLayer(layer => {
      const feature = (layer as any).feature;
      const id = feature?.properties?.id;
      if (!id) return;
      layer.on('click', () => this.state.seleccionarParcela(id));
    });
  }

  private engancharSeleccionLote(capa: L.Layer): void {
    if (!(capa instanceof L.GeoJSON)) return;
    capa.eachLayer(layer => {
      const feature = (layer as any).feature;
      const id = feature?.properties?.id;
      if (!id) return;
      layer.on('click', () => this.state.seleccionarLote(id));
    });
  }

  private aplicarResaltadoSeleccion(): void {
    const selId = this.state.parcelaSeleccionadaId();
    if (!this.capaParcelas || !(this.capaParcelas instanceof L.GeoJSON)) return;
    this.capaParcelas.eachLayer(layer => {
      const path = layer as L.Path;
      if (!path.setStyle) return;
      const esSeleccionada = (layer as any).feature?.properties?.id === selId;
      path.setStyle({ weight: esSeleccionada ? 4 : 1.5 });
      if (esSeleccionada) path.bringToFront?.();
    });
  }

  private aplicarResaltadoLote(): void {
    const selId = this.state.loteSeleccionadoId();
    if (!this.capaLotes || !(this.capaLotes instanceof L.GeoJSON)) return;
    this.capaLotes.eachLayer(layer => {
      const path = layer as L.Path;
      if (!path.setStyle) return;
      const esSeleccionado = (layer as any).feature?.properties?.id === selId;
      path.setStyle({
        weight: esSeleccionado ? 4 : 2.5,
        fillOpacity: esSeleccionado ? 0.12 : 0.04,
      });
      if (esSeleccionado) path.bringToFront?.();
    });
  }
}
