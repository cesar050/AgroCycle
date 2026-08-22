import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AdminService } from '../services/admin.service';
import { AuthService } from '../../auth/services/auth.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, DecimalPipe],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.scss'
})
export class AdminDashboardComponent implements OnInit {

  cargando    = signal(true);
  usuarios    = signal<any[]>([]);
  temporadas  = signal<any[]>([]);

  constructor(
    private svc: AdminService,
    public auth: AuthService,
  ) {}

  ngOnInit() { this.cargarDatos(); }

  cargarDatos() {
    this.cargando.set(true);

    this.svc.listarUsuarios({ por_pagina: 100 }).subscribe({
      next: (r) => {
        this.usuarios.set(r.usuarios || []);
      },
      error: () => {},
    });

    this.svc.listarTemporadas().subscribe({
      next: (r) => {
        this.temporadas.set(r.temporadas || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  get totalUsuarios()     { return this.usuarios().length; }
  get totalActivos()      { return this.usuarios().filter(u => u.activo).length; }
  get totalAgricultores() { return this.usuarios().filter(u => u.rol === 'agricultor').length; }
  get totalAgronomos()    { return this.usuarios().filter(u => u.rol === 'agronomo').length; }
  get totalTemporadas()   { return this.temporadas().length; }
  get temporadasActivas() { return this.temporadas().filter(t => t.estado === 'activa').length; }

  get ultimosUsuarios(): any[] {
    return [...this.usuarios()]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);
  }

  get nombreCorto(): string {
    return this.auth.usuarioActual()?.nombre?.split(' ')?.[0] || 'Admin';
  }

  colorRol(rol: string): string {
    if (rol === 'agricultor') return 'tag--verde';
    if (rol === 'agronomo')   return 'tag--azul';
    return 'tag--gris';
  }
}