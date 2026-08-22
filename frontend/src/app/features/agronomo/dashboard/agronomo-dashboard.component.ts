import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AgronomoService } from '../services/agronomo.service';
import { AuthService } from '../../auth/services/auth.service';

@Component({
  selector: 'app-agronomo-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './agronomo-dashboard.component.html',
  styleUrl: './agronomo-dashboard.component.scss'
})
export class AgronomoDashboardComponent implements OnInit {

  cargando        = signal(true);
  temporadas      = signal<any[]>([]);
  recomendaciones = signal<any[]>([]);
  observaciones   = signal<any[]>([]);

  constructor(
    private svc: AgronomoService,
    public authService: AuthService,
  ) {}

  ngOnInit() { this.cargarDatos(); }

  cargarDatos() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa');
        if (activa) {
          this.cargarRecomendaciones(activa.id);
          this.cargarObservaciones(activa.id);
        }
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarRecomendaciones(temporadaId: string) {
    this.svc.listarRecomendaciones(temporadaId).subscribe({
      next: (r) => this.recomendaciones.set(r.recomendaciones || []),
      error: () => {},
    });
  }

  cargarObservaciones(temporadaId: string) {
    this.svc.listarObservaciones(temporadaId).subscribe({
      next: (r) => this.observaciones.set(r.observaciones || []),
      error: () => {},
    });
  }

  get temporadaActiva(): any {
    return this.temporadas().find(t => t.estado === 'activa');
  }

  get nombreCorto(): string {
    return this.authService.usuarioActual()?.nombre?.split(' ')?.[0] || 'Agrónomo';
  }

  get totalFincas(): number {
    const ids = new Set(this.temporadas().map((t: any) => t.finca));
    return ids.size;
  }
}