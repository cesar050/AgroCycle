import {
  Component, ElementRef, OnDestroy,
  computed, effect, inject, signal, viewChild,
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import * as L from 'leaflet';

import { MapaService } from '../../services/mapa.service';
import { LeafletMapaService } from '../../services/leaflet-mapa.service';
import { MapaStateService } from '../../services/mapa-state.service';
import { construirGeoJSONParcelas, calcularCentro } from '../../mapa.utils';
import { colorHumedadTecnico, clasificacionHumedad, colorKsFinalTecnico, clasificacionKsFinal } from '../shared/colores-tecnicos';

@Component({
  selector: 'app-mapa-humedad',
  standalone: true,
  imports: [CommonModule, DecimalPipe],
  providers: [MapaStateService],
  templateUrl: './mapa-humedad.component.html',
  styleUrl: './mapa-humedad.component.scss',
})
export class MapaHumedadComponent implements OnDestroy {
  state = inject(MapaStateService);
  private mapaService = inject(MapaService);
  private leafletMapaService = inject(LeafletMapaService);

  mapaElRef  = viewChild<ElementRef>('mapaLeaflet');
  leafletMap = signal<L.Map | null>(null);
  pantallaCompleta = signal(false);

  clasificacionHumedad = clasificacionHumedad;
  clasificacionKsFinal = clasificacionKsFinal;
  colorKsFinalTecnico = colorKsFinalTecnico;

  private capaChoropletica: L.Layer | null = null;
  private cargandoHumedad = false;

  parcelasConHumedad = computed(() => {
    const humedad = this.state.humedadPorParcela();
    return this.state.parcelas().map(p => ({
      parcela: p,
      humedad: humedad.get(p.id),
    }));
  });

  humedadMedia = computed(() => {
    const lista = [...this.state.humedadPorParcela().values()];
    if (!lista.length) return null;
    return lista.reduce((s, h) => s + (h.normalizado || 0), 0) / lista.length;
  });

  // Promedio de Ks_deficit/Ks_exceso/Ks_final sobre las parcelas que ya
  // tienen dato de humedad — null mientras no haya ninguna (el backend
  // los omite si Open-Meteo no respondió para esa parcela).
  ksMedio = computed(() => {
    const lista = [...this.state.humedadPorParcela().values()].filter(h => h.ks_final != null);
    if (!lista.length) return null;
    const promedio = (campo: 'ks_deficit' | 'ks_exceso' | 'ks_final') =>
      lista.reduce((s, h) => s + (h[campo] ?? 0), 0) / lista.length;
    return {
      deficit: promedio('ks_deficit'),
      exceso: promedio('ks_exceso'),
      final: promedio('ks_final'),
    };
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

    // 2) Humedad del suelo: esta vista existe exclusivamente para
    // mostrarla, así que se pide siempre (a diferencia de Mapa normal).
    effect(() => {
      const finca = this.state.fincaActiva();
      if (!finca || this.state.datosHumedad() || this.cargandoHumedad) return;
      this.cargandoHumedad = true;
      this.mapaService.obtenerHumedadFinca(finca.id).subscribe({
        next: (r) => { this.state.datosHumedad.set(r); this.cargandoHumedad = false; },
        error: () => { this.cargandoHumedad = false; },
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

    // 4) Recoloreado coroplético por humedad (rojo/verde/azul).
    effect(() => {
      const mapa = this.leafletMap();
      const datos = this.state.datosMapa();
      const humedadPorParcela = this.state.humedadPorParcela();
      if (!mapa || !datos?.finca) return;

      if (this.capaChoropletica) {
        mapa.removeLayer(this.capaChoropletica);
        this.capaChoropletica = null;
      }

      const geojsonParcelas = construirGeoJSONParcelas(datos.finca);
      const capa = L.geoJSON(geojsonParcelas, {
        style: (feature) => {
          const id = feature?.properties?.['id'];
          const h = humedadPorParcela.get(id);
          const normalizado = h?.normalizado ?? 0.5;
          return {
            color: '#FFFFFF', weight: 1.5,
            fillColor: h ? colorHumedadTecnico(normalizado) : '#CBD5E1',
            fillOpacity: 0.7,
          };
        },
        onEachFeature: (feature, layer) => {
          const nombre = feature?.properties?.['nombre'] ?? 'Parcela';
          const id = feature?.properties?.['id'];
          const h = humedadPorParcela.get(id);
          const texto = h
            ? `${h.humedad_m3m3.toFixed(2)} m³/m³ · ${clasificacionHumedad(h.normalizado)}`
            : 'Sin dato de humedad';
          layer.bindTooltip(`<strong>${nombre}</strong><br>${texto}`, { sticky: true });
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
