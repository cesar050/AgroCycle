import {
  Component, OnDestroy, signal,
  AfterViewInit, ElementRef, ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MapaService } from '../../services/mapa.service';

@Component({
  selector: 'app-nueva-parcela',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './nueva-parcela.component.html',
  styleUrl: './nueva-parcela.component.scss'
})
export class NuevaParcelaComponent implements AfterViewInit, OnDestroy {

  @ViewChild('mapaRef') mapaRef!: ElementRef;

  loteId  = '';
  fincaId = '';
  lote    = signal<any>(null);
  finca   = signal<any>(null);

  // Formulario
  nombre       = '';
  tipoSueloId  = '';
  drenaje      = 'moderado';
  accesoRiego  = false;
  tipoRiego    = '';

  // Estado
  cargando    = signal(false);
  error       = signal('');
  coordenadas = signal<[number,number][]>([]);
  areaHa      = signal(0);

  tiposSuelo = [
    { id: 1, nombre: 'Franco arenoso' },
    { id: 2, nombre: 'Franco arcilloso' },
    { id: 3, nombre: 'Arcilloso' },
    { id: 4, nombre: 'Arenoso' },
    { id: 5, nombre: 'Limoso' },
  ];

  drenajeOpciones = ['bueno', 'moderado', 'deficiente'];
  tiposRiego = ['Ninguno', 'Goteo', 'Aspersión', 'Gravedad', 'Manual'];

  private mapa:         any = null;
  private poligono:     any = null;
  private marcadores:   any[] = [];
  private puntosLatLng: any[] = [];

  constructor(
    private mapaService: MapaService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.loteId  = this.route.snapshot.paramMap.get('lote_id') || '';
    this.cargarDatos();
  }

  cargarDatos() {
    // Cargar lotes de la finca para obtener contexto
    // Primero necesitamos el finca_id del lote
    // Por ahora usamos el mapa general
  }

  ngAfterViewInit() {
    setTimeout(() => this.inicializarMapa(), 200);
  }

  private async inicializarMapa() {
    if (!this.mapaRef?.nativeElement || this.mapa) return;
    const L = await import('leaflet');

    this.mapa = L.map(this.mapaRef.nativeElement, {
      center: [-4.0876, -79.8193],
      zoom: 16,
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

    this.mapa.on('click', (e: any) => this.agregarPunto(e.latlng, L));
  }

  private agregarPunto(latlng: any, L: any) {
    const marker = L.circleMarker(latlng, {
      radius: 5, fillColor: '#2E7D32',
      color: '#fff', weight: 2, fillOpacity: 1,
    }).addTo(this.mapa);

    this.puntosLatLng.push(latlng);
    this.marcadores.push(marker);

    if (this.poligono) this.mapa.removeLayer(this.poligono);

    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#2E7D32', weight: 2,
        fillColor: '#2E7D32', fillOpacity: 0.35,
      }).addTo(this.mapa);
      const areaM2 = this.calcularAreaM2(this.puntosLatLng);
      this.areaHa.set(Math.round(areaM2 / 10000 * 100) / 100);
    }

    this.coordenadas.set(this.puntosLatLng.map(p => [p.lng, p.lat]));
  }

  private calcularAreaM2(puntos: any[]): number {
    const R = 6371000;
    let area = 0;
    const n = puntos.length;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      const xi = puntos[i].lng * (Math.PI/180) * R * Math.cos(puntos[i].lat * Math.PI/180);
      const yi = puntos[i].lat * (Math.PI/180) * R;
      const xj = puntos[j].lng * (Math.PI/180) * R * Math.cos(puntos[j].lat * Math.PI/180);
      const yj = puntos[j].lat * (Math.PI/180) * R;
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
        color: '#2E7D32', weight: 2, fillColor: '#2E7D32', fillOpacity: 0.35,
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
      nombre:       this.nombre.trim(),
      coordenadas:  this.coordenadas(),
      tipo_suelo_id: this.tipoSueloId ? parseInt(this.tipoSueloId) : null,
      drenaje:      this.drenaje,
      acceso_riego: this.accesoRiego,
      tipo_riego:   this.accesoRiego ? this.tipoRiego : null,
    };

    this.mapaService.registrarParcela(this.loteId, datos).subscribe({
      next: () => {
        this.cargando.set(false);
        this.router.navigate(['/app/mapa']);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'Error al guardar la parcela.');
      }
    });
  }

  ngOnDestroy() { this.mapa?.remove(); this.mapa = null; }
}