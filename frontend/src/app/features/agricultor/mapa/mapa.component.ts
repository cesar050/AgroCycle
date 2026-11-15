import {
  Component, OnDestroy, signal, computed, effect, viewChild, ElementRef, inject,
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import * as L from 'leaflet';

import { MapaService } from './services/mapa.service';
import { LeafletMapaService } from './services/leaflet-mapa.service';
import { MapaStateService, MapaBase, Parcela } from './services/mapa-state.service';
import { PanelGestionarFincaComponent } from './components/panel-gestionar-finca/panel-gestionar-finca.component';
import { PanelGestionarLoteComponent } from './components/panel-gestionar-lote/panel-gestionar-lote.component';
import { PanelGestionarParcelaComponent } from './components/panel-gestionar-parcela/panel-gestionar-parcela.component';
import { construirGeoJSONParcelas, calcularCentro } from './mapa.utils';
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

  mapaElRef = viewChild<ElementRef>('mapaLeaflet');

  // Única variable de UI: colapsa el panel del 20% para que el mapa
  // ocupe el 100% del contenedor, y viceversa.
  pantallaCompleta = signal(false);

  basesMapa = BASES_MAPA;

  private capaParcelas: L.Layer | null = null;

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

      this.state.cargando.set(true);
      this.mapaService.obtenerMapaFinca(finca.id).subscribe({
        next: (res) => { this.state.datosMapa.set(res); this.state.cargando.set(false); },
        error: () => this.state.cargando.set(false),
      });
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

    // 4) Parcelas coloreadas por etapa fenológica — única capa temática
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

    // 5) Resaltado de la parcela seleccionada.
    effect(() => {
      this.state.parcelaSeleccionadaId();
      this.aplicarResaltadoSeleccion();
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

  elegirBase(base: MapaBase): void {
    this.state.mapaBase.set(base);
  }

  toggleVistaCompleta(): void {
    this.pantallaCompleta.update(v => !v);
    setTimeout(() => this.state.mapaLeaflet()?.invalidateSize(), 220);
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
}
