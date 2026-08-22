import {
  Component, OnInit, OnDestroy, signal,
  AfterViewInit, ElementRef, ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MapaFincaComponent } from '../../../shared/components/mapa-finca/mapa-finca.component';
import { MapaService } from './services/mapa.service';
import { AuthService } from '../../auth/services/auth.service';

@Component({
  selector: 'app-mapa',
  standalone: true,
  imports: [CommonModule, RouterLink, MapaFincaComponent],
  templateUrl: './mapa.component.html',
  styleUrl: './mapa.component.scss'
})
export class MapaComponent implements OnInit {

  cargando    = signal(true);
  fincas      = signal<any[]>([]);
  fincaActiva = signal<any>(null);
  datosMapa   = signal<any>(null);
  vistaActiva = signal<'normal' | 'pendiente' | 'humedad'>('normal');
  datosTopografia = signal<any>(null);
  cargandoTopo    = signal(false);

  constructor(
    private mapaService: MapaService,
    public authService: AuthService,
  ) {}

  ngOnInit() {
    this.cargarFincas();
  }

  cargarFincas() {
    this.cargando.set(true);
    this.mapaService.listarFincas().subscribe({
      next: (res) => {
        const lista = Array.isArray(res) ? res : (res.fincas || []);
        this.fincas.set(lista);
        if (lista.length > 0) {
          this.seleccionarFinca(lista[0]);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  seleccionarFinca(finca: any) {
    this.fincaActiva.set(finca);
    this.datosMapa.set(null);
    this.mapaService.obtenerMapaFinca(finca.id).subscribe({
      next: (res) => {
        this.datosMapa.set(res);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cambiarVista(v: 'normal' | 'pendiente' | 'humedad') {
    this.vistaActiva.set(v);
    if (v === 'pendiente' && !this.datosTopografia() && this.fincaActiva()) {
      this.cargarTopografia(this.fincaActiva().id);
    }
  }

  cargarTopografia(fincaId: string) {
    this.cargandoTopo.set(true);
    this.mapaService.obtenerTopografiaFinca(fincaId).subscribe({
      next:  (r) => { this.datosTopografia.set(r); this.cargandoTopo.set(false); },
      error: ()  => this.cargandoTopo.set(false),
    });
  }

  colorPendiente(p: number): string {
  if (p < 5)  return '#2E7D32';
  if (p < 10) return '#8BC34A';
  if (p < 20) return '#FFC107';
  if (p < 35) return '#FF5722';
  return '#D32F2F';
  }

  etiquetaPendiente(p: number): string {
    if (p < 5)  return 'Plano';
    if (p < 10) return 'Suave';
    if (p < 20) return 'Moderado';
    if (p < 35) return 'Pronunciado';
    return 'Muy pronunciado';
  }

  
    // Agrega dentro de la clase MapaComponent:

  leyendaEtapas = [
    { etapa: 'pre_siembra',           label: 'Sin preparar',  color: '#5E3B1E' },
    { etapa: 'emergencia',            label: 'Emergencia',    color: '#7FBF3F' },
    { etapa: 'crecimiento_vegetativo',label: 'Crecimiento',   color: '#4E9F3D' },
    { etapa: 'floracion',             label: 'Floración',     color: '#2E7D32' },
    { etapa: 'llenado_grano',         label: 'Llenado',       color: '#E8C547' },
    { etapa: 'maduracion',            label: 'Maduración',    color: '#D4A017' },
    { etapa: 'cosecha',               label: 'Cosecha',       color: '#D4A017' },
  ];

  colorEtapa(etapa: string): string {
    return this.leyendaEtapas.find(e => e.etapa === etapa)?.color || '#5E3B1E';
  }

  etiquetaEtapa(etapa: string): string {
    const etiquetas: Record<string,string> = {
      pre_siembra: 'Pre-siembra',
      emergencia: 'Emergencia',
      crecimiento_vegetativo: 'Crecimiento',
      floracion: 'Floración',
      llenado_grano: 'Llenado',
      maduracion: 'Maduración',
      cosecha: 'Cosecha',
    };
    return etiquetas[etapa] || etapa;
  }

  get totalLotes(): number {
    return this.datosMapa()?.finca?.lotes?.length || 0;
  }

  get totalParcelas(): number {
    return (this.datosMapa()?.finca?.lotes || [])
      .reduce((s: number, l: any) => s + (l.parcelas?.length || 0), 0);
  }

  get superficieTotal(): number {
    return this.fincaActiva()?.superficie_ha || 0;
  }
}