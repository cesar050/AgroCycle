import {
  Component, ElementRef, OnDestroy,
  computed, effect, inject, signal, viewChild,
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import * as L from 'leaflet';

import { MapaService } from '../../services/mapa.service';
import { LeafletMapaService } from '../../services/leaflet-mapa.service';
import { MapaStateService } from '../../services/mapa-state.service';
import { construirGeoJSONParcelas, calcularCentro, etiquetaPendiente } from '../../mapa.utils';
import { colorPendienteTecnico, clasificacionPendiente } from '../shared/colores-tecnicos';

@Component({
  selector: 'app-mapa-pendiente',
  standalone: true,
  imports: [CommonModule, DecimalPipe],
  providers: [MapaStateService],
  templateUrl: './mapa-pendiente.component.html',
  styleUrl: './mapa-pendiente.component.scss',
})
export class MapaPendienteComponent implements OnDestroy {
  state = inject(MapaStateService);
  private mapaService = inject(MapaService);
  private leafletMapaService = inject(LeafletMapaService);

  mapaElRef  = viewChild<ElementRef>('mapaLeaflet');
  leafletMap = signal<L.Map | null>(null);

  // Única variable de UI de esta vista: colapsa el panel del 40% para
  // que el mapa ocupe el 100% del contenedor, y viceversa.
  pantallaCompleta = signal(false);

  etiquetaPendiente = etiquetaPendiente;
  clasificacionPendiente = clasificacionPendiente;

  private capaChoropletica: L.Layer | null = null;
  private cargandoTopo = false;

  parcelasConTopo = computed(() => {
    const topo = this.state.topografiaPorParcela();
    return this.state.parcelas().map(p => ({
      parcela: p,
      topo: topo.get(p.id),
      pendiente: topo.get(p.id)?.pendiente ?? p.pendiente,
    }));
  });

  pendienteMedia = computed(() => {
    const lista = this.state.parcelas();
    if (!lista.length) return null;
    return lista.reduce((s, p) => s + (p.pendiente || 0), 0) / lista.length;
  });

  constructor() {
    // 1) Cargar datos de finca (igual patrón que MapaComponent).
    effect(() => {
      const finca = this.state.fincaActiva();
      const cargandoFincas = this.state.cargandoFincas();
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

    // 2) Topografía: esta vista existe exclusivamente para mostrarla, así
    // que se pide siempre (a diferencia de Mapa normal, donde es opcional
    // bajo demanda del usuario).
    effect(() => {
      const finca = this.state.fincaActiva();
      if (!finca || this.state.datosTopografia() || this.cargandoTopo) return;
      this.cargandoTopo = true;
      this.mapaService.obtenerTopografiaFinca(finca.id).subscribe({
        next: (r) => { this.state.datosTopografia.set(r); this.cargandoTopo = false; },
        error: () => { this.cargandoTopo = false; },
      });
    });

    // 3) Ciclo de vida del mapa Leaflet.
    effect(() => {
      const el = this.mapaElRef()?.nativeElement;
      if (!el) return;

      const datos = this.state.datosMapa();
      if (!datos?.finca) return;

      const centro = calcularCentro(datos.finca.geojson);
      if (!centro) return;

      this.leafletMapaService.destroy();
      const mapa = this.leafletMapaService.initMap(el.id, centro, 15);

      if (datos.finca.geojson) {
        this.leafletMapaService.agregarLimiteFinca(mapa, datos.finca.geojson);
        this.leafletMapaService.fitBounds(mapa, datos.finca.geojson);
      }

      this.leafletMap.set(mapa);
    });

    // 4) Recoloreado coroplético por pendiente (rojo/verde/azul).
    effect(() => {
      const mapa = this.leafletMap();
      const datos = this.state.datosMapa();
      const topoPorParcela = this.state.topografiaPorParcela();
      if (!mapa || !datos?.finca) return;

      if (this.capaChoropletica) {
        mapa.removeLayer(this.capaChoropletica);
        this.capaChoropletica = null;
      }

      const geojsonParcelas = construirGeoJSONParcelas(datos.finca);
      const capa = L.geoJSON(geojsonParcelas, {
        style: (feature) => {
          const id = feature?.properties?.['id'];
          const t = topoPorParcela.get(id);
          const pendiente = t?.pendiente ?? 0;
          return {
            color: '#FFFFFF', weight: 1.5,
            fillColor: colorPendienteTecnico(pendiente),
            fillOpacity: 0.7,
          };
        },
        onEachFeature: (feature, layer) => {
          const nombre = feature?.properties?.['nombre'] ?? 'Parcela';
          const id = feature?.properties?.['id'];
          const t = topoPorParcela.get(id);
          const pendiente = t?.pendiente ?? 0;
          layer.bindTooltip(
            `<strong>${nombre}</strong><br>${pendiente.toFixed(1)}% · ${clasificacionPendiente(pendiente)}`,
            { sticky: true }
          );
        },
      }).addTo(mapa);

      this.capaChoropletica = capa;
    });
  }

  ngOnDestroy(): void {
    this.leafletMapaService.destroy();
  }

  toggleVistaCompleta(): void {
    this.pantallaCompleta.update(v => !v);
    setTimeout(() => this.leafletMap()?.invalidateSize(), 220);
  }
}
