import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TemporadaService } from './services/temporada.service';

@Component({
  selector: 'app-temporada',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './temporada.component.html',
  styleUrl: './temporada.component.scss'
})
export class TemporadaComponent implements OnInit {

  cargando   = signal(true);
  temporadas = signal<any[]>([]);
  comparativo = signal<any>(null);

  constructor(private svc: TemporadaService) {}

  ngOnInit() { this.cargar(); }

  cargar() {
    this.cargando.set(true);
    this.svc.listar().subscribe({
      next: (res) => {
        this.temporadas.set(res.temporadas || []);
        this.comparativo.set(res.comparativo || null);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  get activas()  { return this.temporadas().filter(t => t.estado === 'activa'); }
  get cerradas() { return this.temporadas().filter(t => t.estado === 'cerrada'); }
  get otras()    { return this.temporadas().filter(
    t => t.estado !== 'activa' && t.estado !== 'cerrada'
  ); }

  badgeEstado(estado: string): string {
    const map: Record<string, string> = {
      activa:    'tag--verde',
      cerrada:   'tag--gris',
      cancelada: 'tag--rojo',
      pausada:   'tag--naranja',
    };
    return map[estado] || 'tag--gris';
  }

  labelEstado(estado: string): string {
    const map: Record<string, string> = {
      activa:    'Activa',
      cerrada:   'Cerrada',
      cancelada: 'Cancelada',
      pausada:   'Pausada',
    };
    return map[estado] || estado;
  }
}