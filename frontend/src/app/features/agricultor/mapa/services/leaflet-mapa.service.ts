import { Injectable } from '@angular/core';
import * as L from 'leaflet';

@Injectable({ providedIn: 'root' })
export class LeafletMapaService {

  private map: L.Map | null = null;

  initMap(elementId: string, center: [number, number], zoom: number): L.Map {
    this.map = L.map(elementId, {
      center,
      zoom,
      zoomControl: false,
      maxZoom: 19,
      minZoom: 10,
    });

    // Capa base satélite
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { attribution: 'Esri', maxZoom: 19, maxNativeZoom: 17 }
    ).addTo(this.map);

    // Control de zoom en esquina superior izquierda
    L.control.zoom({ position: 'topleft' }).addTo(this.map);

    return this.map;
  }

  agregarCapaParcelas(map: L.Map, geojson: any, colores: Record<string, string>): L.Layer {
    return L.geoJSON(geojson, {
      style: (feature) => ({
        color: '#FFFFFF',
        weight: 1.5,
        fillColor: colores[feature?.properties?.['etapa']] ?? '#81C784',
        fillOpacity: 0.5,
      }),
      onEachFeature: (feature, layer) => {
        const p = feature?.properties ?? {};
        layer.bindTooltip(
          `<strong>${p['nombre'] ?? 'Parcela'}</strong><br>${p['etapa'] ?? ''}`,
          { sticky: true }
        );
      },
    }).addTo(map);
  }

  agregarLimiteFinca(map: L.Map, geojson: any): L.Layer {
    return L.geoJSON(geojson, {
      style: {
        color: '#FFFFFF',
        weight: 2.5,
        opacity: 0.9,
        fillOpacity: 0,
        dashArray: '6, 4',
      },
    }).addTo(map);
  }

  fitBounds(map: L.Map, geojson: any): void {
    try {
      const layer = L.geoJSON(geojson);
      map.fitBounds(layer.getBounds(), { padding: [30, 30] });
    } catch {
      // geojson vacío o inválido: se ignora, el mapa queda en el centro calculado
    }
  }

  destroy(): void {
    this.map?.remove();
    this.map = null;
  }
}
