import {
  Component, OnInit, OnDestroy, signal,
  AfterViewInit, ElementRef, ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MapaService } from '../../services/mapa.service';

@Component({
  selector: 'app-nuevo-lote',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './nuevo-lote.component.html',
  styleUrl: './nuevo-lote.component.scss'
})
export class NuevoLoteComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('mapaRef') mapaRef!: ElementRef;

  fincaId    = '';
  finca      = signal<any>(null);

  // Formulario
  nombre     = '';
  descripcion = '';

  // Estado
  cargando    = signal(false);
  error       = signal('');
  coordenadas = signal<[number,number][]>([]);
  areaHa      = signal(0);

  // Validación de puntos dentro de la finca
  puntoCercaDeLimite = signal(false);
  mensajeError       = signal('');

  private mapa:      any = null;
  private poligono:  any = null;
  private marcadores: any[] = [];
  private puntosLatLng: any[] = [];
  private contornoFinca: any = null;

  constructor(
    private mapaService: MapaService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.fincaId = this.route.snapshot.paramMap.get('finca_id') || '';
    this.cargarFinca();
  }

  cargarFinca() {
    this.mapaService.obtenerMapaFinca(this.fincaId).subscribe({
      next: (res) => {
        this.finca.set(res.finca);
        // Inicializar mapa después de tener los datos
        setTimeout(() => this.inicializarMapa(res.finca), 100);
      },
      error: () => {},
    });
  }

  ngAfterViewInit() {}

  private async inicializarMapa(finca: any) {
    if (!this.mapaRef?.nativeElement || this.mapa) return;
    const L = await import('leaflet');

    // Calcular centro de la finca
    let centro: [number, number] = [-4.0876, -79.8193];
    let zoom = 16;

    if (finca.geojson?.coordinates?.[0]) {
      const coords = finca.geojson.coordinates[0];
      const lats = coords.map((c: number[]) => c[1]);
      const lngs = coords.map((c: number[]) => c[0]);
      centro = [
        (Math.min(...lats) + Math.max(...lats)) / 2,
        (Math.min(...lngs) + Math.max(...lngs)) / 2,
      ];
    }

    this.mapa = L.map(this.mapaRef.nativeElement, {
      center: centro,
      zoom,
      zoomControl: true,
      attributionControl: false,
    });

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21 }
    ).addTo(this.mapa);

    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21, opacity: 0.6 }
    ).addTo(this.mapa);

    // Dibujar contorno de la finca como referencia
    if (finca.geojson?.coordinates?.[0]) {
      const coords = finca.geojson.coordinates[0].map(
        (c: number[]) => [c[1], c[0]] as [number, number]
      );
      this.contornoFinca = L.polygon(coords, {
        color: '#2E7D32',
        weight: 2,
        fillColor: '#2E7D32',
        fillOpacity: 0.08,
        dashArray: '6,4',
      }).addTo(this.mapa);

      this.mapa.fitBounds(this.contornoFinca.getBounds(), { padding: [30, 30] });
    }

    // Dibujar lotes existentes
    (finca.lotes || []).forEach((lote: any) => {
      if (lote.geojson?.coordinates?.[0]) {
        const coords = lote.geojson.coordinates[0].map(
          (c: number[]) => [c[1], c[0]] as [number, number]
        );
        L.polygon(coords, {
          color: '#7BAF82',
          weight: 1.5,
          fillColor: '#7BAF82',
          fillOpacity: 0.2,
        }).addTo(this.mapa).bindTooltip(lote.nombre, {
          permanent: true, direction: 'center', className: 'lote-label'
        });
      }
    });

    // Click para agregar puntos del nuevo lote
    this.mapa.on('click', (e: any) => this.agregarPunto(e.latlng, L));
  }

  private agregarPunto(latlng: any, L: any) {
    // Validar que el punto esté dentro del contorno de la finca
    if (!this.puntoEnFinca(latlng)) {
      this.mensajeError.set(
        'El punto está fuera del límite de la finca. Colócalo dentro del área delimitada.'
      );
      this.mostrarErrorEnMapa(latlng, L);
      return;
    }
    this.mensajeError.set('');

    const marker = L.circleMarker(latlng, {
      radius:      5,
      fillColor:   '#F57C00',
      color:       '#fff',
      weight:      2,
      fillOpacity: 1,
    }).addTo(this.mapa);

    this.puntosLatLng.push(latlng);
    this.marcadores.push(marker);

    if (this.poligono) this.mapa.removeLayer(this.poligono);

    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color:       '#F57C00',
        weight:      2,
        fillColor:   '#F57C00',
        fillOpacity: 0.3,
      }).addTo(this.mapa);

      const areaM2 = this.calcularAreaM2(this.puntosLatLng);
      this.areaHa.set(Math.round(areaM2 / 10000 * 100) / 100);
    }

    this.coordenadas.set(this.puntosLatLng.map(p => [p.lng, p.lat]));
  }

  private puntoEnFinca(latlng: any): boolean {
    const finca = this.finca();
    if (!finca?.geojson?.coordinates?.[0]) return true; // Si no hay contorno, permitir
    const coords = finca.geojson.coordinates[0];
    return this.puntoDentroDePoligono(
      latlng.lat, latlng.lng, coords
    );
  }

  private puntoDentroDePoligono(
    lat: number, lng: number, poligono: number[][]
  ): boolean {
    // Algoritmo Ray Casting
    let dentro = false;
    const n = poligono.length;
    for (let i = 0, j = n - 1; i < n; j = i++) {
      const xi = poligono[i][0], yi = poligono[i][1];
      const xj = poligono[j][0], yj = poligono[j][1];
      const intersecta = ((yi > lat) !== (yj > lat)) &&
        (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi);
      if (intersecta) dentro = !dentro;
    }
    return dentro;
  }

  private mostrarErrorEnMapa(latlng: any, L: any) {
    // Punto rojo temporal que desaparece
    const marcadorError = L.circleMarker(latlng, {
      radius: 10,
      fillColor: '#D32F2F',
      color: '#D32F2F',
      weight: 2,
      fillOpacity: 0.4,
    }).addTo(this.mapa);

    // Overlay rojo en la pantalla
    this.puntoCercaDeLimite.set(true);
    setTimeout(() => {
      this.mapa.removeLayer(marcadorError);
      this.puntoCercaDeLimite.set(false);
      this.mensajeError.set('');
    }, 2000);
  }

  private calcularAreaM2(puntos: any[]): number {
    const R = 6371000;
    let area = 0;
    const n = puntos.length;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const xi = puntos[i].lng * (Math.PI / 180) * R * Math.cos(puntos[i].lat * Math.PI / 180);
      const yi = puntos[i].lat * (Math.PI / 180) * R;
      const xj = puntos[j].lng * (Math.PI / 180) * R * Math.cos(puntos[j].lat * Math.PI / 180);
      const yj = puntos[j].lat * (Math.PI / 180) * R;
      area += xi * yj - xj * yi;
    }
    return Math.abs(area / 2);
  }

  async deshacerUltimoPunto() {
    if (!this.puntosLatLng.length) return;
    const L = await import('leaflet');
    this.mapa.removeLayer(this.marcadores.pop());
    this.puntosLatLng.pop();
    if (this.poligono) { this.mapa.removeLayer(this.poligono); this.poligono = null; }
    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#F57C00', weight: 2, fillColor: '#F57C00', fillOpacity: 0.3,
      }).addTo(this.mapa);
      this.areaHa.set(Math.round(this.calcularAreaM2(this.puntosLatLng) / 10000 * 100) / 100);
    } else {
      this.areaHa.set(0);
    }
    this.coordenadas.set(this.puntosLatLng.map(p => [p.lng, p.lat]));
  }

  async limpiarMapa() {
    this.marcadores.forEach(m => this.mapa.removeLayer(m));
    this.marcadores = []; this.puntosLatLng = [];
    if (this.poligono) { this.mapa.removeLayer(this.poligono); this.poligono = null; }
    this.coordenadas.set([]); this.areaHa.set(0);
  }

  get puntosDefinidos() { return this.puntosLatLng.length; }

  get puedeGuardar() {
    return this.nombre.trim().length > 0 && this.coordenadas().length >= 3;
  }

  guardar() {
    if (!this.puedeGuardar) {
      this.error.set('Completa el nombre y dibuja al menos 3 puntos.');
      return;
    }
    this.cargando.set(true);
    this.error.set('');

    const datos = {
      nombre:      this.nombre.trim(),
      descripcion: this.descripcion.trim(),
      coordenadas: this.coordenadas(),
    };

    this.mapaService.registrarLote(this.fincaId, datos).subscribe({
      next: () => {
        this.cargando.set(false);
        this.router.navigate(['/app/mapa']);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'Error al guardar el lote.');
      }
    });
  }

  ngOnDestroy() { this.mapa?.remove(); this.mapa = null; }
}