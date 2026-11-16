import { Injectable, signal } from '@angular/core';

export type TipoNotificacion = 'exito' | 'error' | 'advertencia';

export interface Notificacion {
  id: number;
  tipo: TipoNotificacion;
  mensaje: string;
}

const DURACION_MS: Record<TipoNotificacion, number> = {
  exito: 4000,
  advertencia: 5500,
  error: 7000,
};

// Servicio reactivo unico de feedback para toda la app (Signals, sin
// NgRx ni librerias externas). Cualquier flujo CRUD (fincas, lotes,
// parcelas, temporadas, actividades, finanzas...) llama a exito()/error()
// en vez de silenciar el resultado en un signal local — así ningún
// guardado, edición o eliminación pasa desapercibido, y ningún error
// HTTP (400/404/409/500) queda sin mostrarse.
@Injectable({ providedIn: 'root' })
export class NotificacionService {
  private contador = 0;

  notificaciones = signal<Notificacion[]>([]);

  exito(mensaje: string): void {
    this.emitir('exito', mensaje);
  }

  error(mensaje: string): void {
    this.emitir('error', mensaje);
  }

  advertencia(mensaje: string): void {
    this.emitir('advertencia', mensaje);
  }

  // Extrae el mensaje legible que el backend ya devuelve en
  // { "error": "..." } para cualquier codigo HTTP de error, y lo
  // muestra. Nunca se traga el error en silencio: si la respuesta no
  // trae un mensaje reconocible, cae a `fallback`.
  errorHttp(err: unknown, fallback = 'Ocurrió un error inesperado. Intenta de nuevo.'): void {
    const httpError = err as { error?: { error?: string; message?: string }; message?: string } | null;
    const mensaje = httpError?.error?.error || httpError?.error?.message || httpError?.message || fallback;
    this.error(mensaje);
  }

  cerrar(id: number): void {
    this.notificaciones.update(lista => lista.filter(n => n.id !== id));
  }

  private emitir(tipo: TipoNotificacion, mensaje: string): void {
    const id = ++this.contador;
    this.notificaciones.update(lista => [...lista, { id, tipo, mensaje }]);
    setTimeout(() => this.cerrar(id), DURACION_MS[tipo]);
  }
}
