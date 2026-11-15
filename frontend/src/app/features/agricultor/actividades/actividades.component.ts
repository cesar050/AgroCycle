import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ActividadesService } from './services/actividades.service';

@Component({
  selector: 'app-actividades',
  standalone: true,
  imports: [CommonModule, RouterLink, DecimalPipe],
  templateUrl: './actividades.component.html',
  styleUrl: './actividades.component.scss'
})
export class ActividadesComponent implements OnInit {

  cargando    = signal(true);
  error       = signal('');

  temporadas  = signal<any[]>([]);
  temporadaId = signal('');
  actividades = signal<any[]>([]);

  // Filtros
  filtroTipo  = signal('');
  filtroFecha = signal('');

  tiposActividad = [
    { id: 1, nombre: 'Preparación del terreno' },
    { id: 2, nombre: 'Siembra' },
    { id: 3, nombre: 'Fertilización' },
    { id: 4, nombre: 'Control fitosanitario' },
    { id: 5, nombre: 'Riego' },
    { id: 6, nombre: 'Mano de obra' },
    { id: 7, nombre: 'Cosecha' },
    { id: 8, nombre: 'Monitoreo' },
    { id: 9, nombre: 'Otro' },
  ];

  constructor(private svc: ActividadesService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa');
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarActividades(activa.id);
        } else if (lista.length > 0) {
          this.temporadaId.set(lista[0].id);
          this.cargarActividades(lista[0].id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarActividades(temporadaId: string) {
    this.cargando.set(true);
    this.svc.listarPorTemporada(temporadaId).subscribe({
      next: (res) => {
        this.actividades.set(res.actividades || res || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cambiarTemporada(id: string) {
    this.temporadaId.set(id);
    this.cargarActividades(id);
  }

  get actividadesFiltradas(): any[] {
    return this.actividades().filter(a => {
      const okTipo  = !this.filtroTipo() ||
        String(a.tipo_actividad_id) === this.filtroTipo();
      const okFecha = !this.filtroFecha() ||
        a.fecha?.startsWith(this.filtroFecha());
      return okTipo && okFecha;
    });
  }

  get totalCosto(): number {
    return this.actividadesFiltradas.reduce(
      (s, a) => s + (parseFloat(a.costo_total) || 0), 0
    );
  }

  confirmarEliminar(actividad: any) {
    if (!confirm(
      `¿Eliminar la actividad "${this.nombreTipo(actividad.tipo_actividad_id)}" del ${actividad.fecha}?`
    )) return;

    this.svc.eliminar(actividad.id).subscribe({
      next: () => this.cargarActividades(this.temporadaId()),
      error: () => {},
    });
  }

  nombreTipo(id: number): string {
    return this.tiposActividad.find(t => t.id === id)?.nombre || 'Actividad';
  }

  colorTipo(id: number): string {
    const colores: Record<number, string> = {
      1: '#795548', 2: '#4CAF50', 3: '#2196F3',
      4: '#F44336', 5: '#03A9F4', 6: '#FF9800',
      7: '#FFC107', 8: '#9C27B0', 9: '#607D8B',
    };
    return colores[id] || '#607D8B';
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }
}
