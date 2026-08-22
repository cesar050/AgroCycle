import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminService } from '../services/admin.service';

@Component({
  selector: 'app-admin-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-usuarios.component.html',
  styleUrl: './admin-usuarios.component.scss'
})
export class AdminUsuariosComponent implements OnInit {

  cargando    = signal(true);
  guardando   = signal(false);
  usuarios    = signal<any[]>([]);
  usuarioEdit = signal<any>(null);
  error       = signal('');

  filtroRol    = '';
  filtroEstado = '';
  busqueda     = '';

  constructor(private svc: AdminService) {}

  ngOnInit() { this.cargar(); }

  cargar() {
    this.cargando.set(true);
    this.svc.listarUsuarios({ por_pagina: 200 }).subscribe({
      next: (r) => { this.usuarios.set(r.usuarios || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }

  get usuariosFiltrados(): any[] {
    return this.usuarios().filter(u => {
      const okRol    = !this.filtroRol    || u.rol === this.filtroRol;
      const okEstado = !this.filtroEstado ||
        (this.filtroEstado === 'activo'   ? u.activo :
         this.filtroEstado === 'inactivo' ? !u.activo : true);
      const okBusca  = !this.busqueda ||
        u.nombre?.toLowerCase().includes(this.busqueda.toLowerCase()) ||
        u.correo?.toLowerCase().includes(this.busqueda.toLowerCase());
      return okRol && okEstado && okBusca;
    });
  }

  abrirEdicion(u: any) {
    this.usuarioEdit.set({ ...u });
    this.error.set('');
  }

  cerrarEdicion() { this.usuarioEdit.set(null); this.error.set(''); }

  guardarEdicion() {
    const u = this.usuarioEdit();
    if (!u) return;
    this.guardando.set(true);
    this.svc.editarUsuario(u.id, {
      nombre:   u.nombre,
      correo:   u.correo,
      telefono: u.telefono || null,
    }).subscribe({
      next: () => {
        this.guardando.set(false);
        this.cerrarEdicion();
        this.cargar();
      },
      error: (err) => {
        this.guardando.set(false);
        this.error.set(err.error?.error || 'Error al guardar.');
      }
    });
  }

  toggleEstado(u: any) {
    const accion = u.activo ? 'desactivar' : 'activar';
    if (!confirm(`¿Deseas ${accion} a ${u.nombre}?`)) return;

    this.svc.cambiarEstado(u.id, !u.activo).subscribe({
      next: () => {
        this.usuarios.update(lista =>
          lista.map(x => x.id === u.id ? { ...x, activo: !u.activo } : x)
        );
      },
      error: () => {},
    });
  }

  colorRol(rol: string): string {
    if (rol === 'agricultor')    return 'tag--verde';
    if (rol === 'agronomo')      return 'tag--azul';
    if (rol === 'administrador') return 'tag--morado';
    return 'tag--gris';
  }

  iniciales(nombre: string): string {
    const p = (nombre || 'U').trim().split(' ');
    return p.length >= 2
      ? `${p[0][0]}${p[1][0]}`.toUpperCase()
      : p[0]?.[0]?.toUpperCase() || 'U';
  }

  claseAvatar(rol: string): string {
    if (rol === 'agricultor')    return 'verde';
    if (rol === 'agronomo')      return 'azul';
    if (rol === 'administrador') return 'morado';
    return 'gris';
  }
}