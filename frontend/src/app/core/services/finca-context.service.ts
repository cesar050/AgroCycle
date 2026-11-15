import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';

export interface Finca {
  id: string;
  nombre: string;
  ubicacion?: string | null;
  provincia?: string | null;
  canton?: string | null;
  parroquia?: string | null;
  sector?: string | null;
  descripcion?: string | null;
  superficie_ha?: number | null;
  tiene_geometria?: boolean;
  activo?: boolean;
  [key: string]: any;
}

@Injectable({ providedIn: 'root' })
export class FincaContextService {
  private api = inject(ApiService);

  fincas      = signal<Finca[]>([]);
  fincaActiva = signal<Finca | null>(null);
  cargando    = signal(true);

  // Señal de un solo uso: cualquier vista puede pedir que se abra el
  // dropdown de selección de finca del sidebar sin duplicar su lógica.
  // El layout la escucha con effect() y la resetea tras abrir el dropdown.
  selectorAbierto = signal(false);

  constructor() {
    this.cargarFincas();
  }

  cargarFincas(): void {
    this.cargando.set(true);
    this.api.get<any>('/fincas').subscribe({
      next: (res) => {
        const fincas = Array.isArray(res) ? res : (res.fincas || []);
        this.fincas.set(fincas);
        if (fincas.length > 0 && !this.fincaActiva()) {
          this.fincaActiva.set(fincas[0]);
        }
        this.cargando.set(false);
      },
      error: () => {
        this.fincas.set([]);
        this.cargando.set(false);
      },
    });
  }

  seleccionarFinca(finca: Finca): void {
    this.fincaActiva.set(finca);
  }

  // Usado por el panel "Gestionar finca" tras crear una finca nueva:
  // la añade a la lista del selector y la deja activa de inmediato,
  // sin necesidad de recargar /fincas.
  agregarFincaYSeleccionar(finca: Finca): void {
    this.fincas.update(lista => [...lista, finca]);
    this.fincaActiva.set(finca);
  }

  // Usado tras editar una finca: refleja los cambios en la lista del
  // selector y en la finca activa si es la que se edito.
  actualizarFincaEnLista(finca: Finca): void {
    this.fincas.update(lista => lista.map(f => f.id === finca.id ? { ...f, ...finca } : f));
    if (this.fincaActiva()?.id === finca.id) {
      this.fincaActiva.update(f => f ? { ...f, ...finca } : f);
    }
  }

  // Usado tras eliminar una finca: la quita de la lista y, si era la
  // activa, selecciona la siguiente disponible (o ninguna).
  eliminarFincaDeLista(fincaId: string): void {
    this.fincas.update(lista => lista.filter(f => f.id !== fincaId));
    if (this.fincaActiva()?.id === fincaId) {
      this.fincaActiva.set(this.fincas()[0] ?? null);
    }
  }
}
