import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-recomendaciones',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './recomendaciones.component.html',
  styleUrl: './recomendaciones.component.scss'
})
export class RecomendacionesComponent implements OnInit {

  cargando         = signal(true);
  temporadas       = signal<any[]>([]);
  temporadaId      = signal('');
  recomendaciones  = signal<any[]>([]);
  filtroUrgencia   = signal('');
  filtroLeida      = signal('');

  constructor(private api: ApiService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.api.get<any>('/temporadas/historial').subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa') || lista[0];
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarRecomendaciones(activa.id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarRecomendaciones(temporadaId: string) {
    this.cargando.set(true);
    this.temporadaId.set(temporadaId);
    this.api.get<any>(
      `/agronomo/temporadas/${temporadaId}/recomendaciones`
    ).subscribe({
      next: (res) => {
        this.recomendaciones.set(res.recomendaciones || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  marcarLeida(id: string) {
    this.api.patch(`/agronomo/recomendaciones/${id}/leer`, {}).subscribe({
      next: () => {
        this.recomendaciones.update(lista =>
          lista.map(r => r.id === id ? { ...r, leida: true } : r)
        );
      },
      error: () => {},
    });
  }

  get recomendacionesFiltradas(): any[] {
    return this.recomendaciones().filter(r => {
      const okU = !this.filtroUrgencia() || r.urgencia === this.filtroUrgencia();
      const okL = !this.filtroLeida() ||
        (this.filtroLeida() === 'leida' ? r.leida : !r.leida);
      return okU && okL;
    });
  }

  get noLeidas(): number {
    return this.recomendaciones().filter(r => !r.leida).length;
  }

  colorUrgencia(u: string): string {
    if (u === 'alta')  return 'tag--rojo';
    if (u === 'media') return 'tag--naranja';
    return 'tag--verde';
  }

  colorBorde(u: string): string {
    if (u === 'alta')  return '#D32F2F';
    if (u === 'media') return '#F57C00';
    return '#2E7D32';
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }
}