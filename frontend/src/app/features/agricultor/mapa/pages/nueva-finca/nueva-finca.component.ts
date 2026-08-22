import {
  Component, OnInit, OnDestroy, signal,
  AfterViewInit, ElementRef, ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MapaService } from '../../services/mapa.service';

@Component({
  selector: 'app-nueva-finca',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './nueva-finca.component.html',
  styleUrl: './nueva-finca.component.scss'
})
export class NuevaFincaComponent implements AfterViewInit, OnDestroy {

  @ViewChild('mapaRef') mapaRef!: ElementRef;

  // Formulario
  nombre     = '';
  provincia  = 'Loja';
  canton     = 'Paltas';
  parroquia  = 'Guachanama';
  sector     = 'Bramaderos';
  descripcion = '';

  // Estado
  cargando    = signal(false);
  error       = signal('');
  coordenadas = signal<[number,number][]>([]);
  areaHa      = signal(0);

  private mapa:     any = null;
  private poligono: any = null;
  private marcadores: any[] = [];
  private puntosLatLng: any[] = [];

  constructor(
    private mapaService: MapaService,
    private router: Router,
  ) {}

  ngAfterViewInit() {
    setTimeout(() => this.inicializarMapa(), 100);
  }

  private async inicializarMapa() {
    if (!this.mapaRef?.nativeElement) return;
    const L = await import('leaflet');

    this.mapa = L.map(this.mapaRef.nativeElement, {
      center: [-4.0876, -79.8193],
      zoom: 15,
      zoomControl: true,
      attributionControl: false,
    });

    // Satélite
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21 }
    ).addTo(this.mapa);

    // Etiquetas
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 21, opacity: 0.7 }
    ).addTo(this.mapa);

    // Click para agregar puntos
    this.mapa.on('click', (e: any) => {
      this.agregarPunto(e.latlng, L);
    });

    // Instrucción visual
    this.mostrarInstruccion(L);
  }

  private mostrarInstruccion(L: any) {
    const div = L.divIcon({
      className: '',
      html: `<div style="
        background:rgba(0,0,0,0.7);
        color:#fff;
        padding:8px 14px;
        border-radius:6px;
        font-size:12px;
        font-family:Inter,sans-serif;
        white-space:nowrap;
        pointer-events:none;
      ">Haz clic en el mapa para definir los vértices de la finca</div>`,
      iconAnchor: [160, -10],
    });
  }

  private agregarPunto(latlng: any, L: any) {
    const marker = L.circleMarker(latlng, {
      radius: 6,
      fillColor: '#2E7D32',
      color: '#fff',
      weight: 2,
      fillOpacity: 1,
    }).addTo(this.mapa);

    this.puntosLatLng.push(latlng);
    this.marcadores.push(marker);

    // Actualizar polígono
    if (this.poligono) {
      this.mapa.removeLayer(this.poligono);
    }

    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#2E7D32',
        weight: 2,
        fillColor: '#2E7D32',
        fillOpacity: 0.25,
      }).addTo(this.mapa);

      // Calcular área aproximada
      const areaM2 = this.calcularAreaM2(this.puntosLatLng);
      this.areaHa.set(Math.round(areaM2 / 10000 * 100) / 100);
    }

    // Guardar coordenadas como [lng, lat]
    this.coordenadas.set(
      this.puntosLatLng.map(p => [p.lng, p.lat])
    );
  }

  private calcularAreaM2(puntos: any[]): number {
    // Fórmula de Shoelace con proyección aproximada
    const R = 6371000;
    let area = 0;
    const n = puntos.length;

    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const xi = puntos[i].lng * (Math.PI / 180) * R *
        Math.cos(puntos[i].lat * (Math.PI / 180));
      const yi = puntos[i].lat * (Math.PI / 180) * R;
      const xj = puntos[j].lng * (Math.PI / 180) * R *
        Math.cos(puntos[j].lat * (Math.PI / 180));
      const yj = puntos[j].lat * (Math.PI / 180) * R;
      area += xi * yj - xj * yi;
    }

    return Math.abs(area / 2);
  }

  async deshacerUltimoPunto() {
    if (this.puntosLatLng.length === 0) return;
    const L = await import('leaflet');

    this.mapa.removeLayer(this.marcadores.pop());
    this.puntosLatLng.pop();

    if (this.poligono) {
      this.mapa.removeLayer(this.poligono);
      this.poligono = null;
    }

    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#2E7D32',
        weight: 2,
        fillColor: '#2E7D32',
        fillOpacity: 0.25,
      }).addTo(this.mapa);

      const areaM2 = this.calcularAreaM2(this.puntosLatLng);
      this.areaHa.set(Math.round(areaM2 / 10000 * 100) / 100);
    } else {
      this.areaHa.set(0);
    }

    this.coordenadas.set(
      this.puntosLatLng.map(p => [p.lng, p.lat])
    );
  }

  async limpiarMapa() {
    const L = await import('leaflet');
    this.marcadores.forEach(m => this.mapa.removeLayer(m));
    this.marcadores = [];
    this.puntosLatLng = [];
    if (this.poligono) {
      this.mapa.removeLayer(this.poligono);
      this.poligono = null;
    }
    this.coordenadas.set([]);
    this.areaHa.set(0);
  }

  usarUbicacionActual() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(pos => {
      this.mapa.setView(
        [pos.coords.latitude, pos.coords.longitude], 17
      );
    });
  }

  get puntosDefinidos(): number {
    return this.puntosLatLng.length;
  }

  get puedeGuardar(): boolean {
    return this.nombre.trim().length > 0 &&
           this.coordenadas().length >= 3;
  }

  guardar() {
    if (!this.puedeGuardar) {
      this.error.set('Completa el nombre y dibuja al menos 3 puntos en el mapa.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    const datos = {
      nombre:      this.nombre.trim(),
      provincia:   this.provincia.trim(),
      canton:      this.canton.trim(),
      parroquia:   this.parroquia.trim(),
      sector:      this.sector.trim(),
      descripcion: this.descripcion.trim(),
      coordenadas: this.coordenadas(),
    };

    this.mapaService.registrarFinca(datos).subscribe({
      next: (res) => {
        this.cargando.set(false);
        this.router.navigate(['/app/mapa']);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.error?.error || 'Error al guardar la finca. Intenta de nuevo.'
        );
      }
    });
  }

  ngOnDestroy() {
    this.mapa?.remove();
    this.mapa = null;
  }
}