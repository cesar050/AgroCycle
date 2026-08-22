import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgronomoService } from '../services/agronomo.service';

@Component({
  selector: 'app-evaluaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './evaluaciones.component.html',
  styleUrl: './evaluaciones.component.scss'
})
export class EvaluacionesComponent implements OnInit {

  cargando     = signal(true);
  guardando    = signal(false);
  mostrarForm  = signal(false);
  errorForm    = signal('');

  temporadas   = signal<any[]>([]);
  temporadaId  = signal('');
  evaluaciones = signal<any[]>([]);

  form = {
    fecha:              '',
    estado_general:     'bueno',
    humedad_suelo:      '',
    temperatura_campo:  '',
    ndvi:               '',
    observaciones:      '',
  };

  estados = [
    { id: 'bueno',     label: 'Bueno',     color: 'tag--verde' },
    { id: 'regular',   label: 'Regular',   color: 'tag--naranja' },
    { id: 'malo',      label: 'Malo',      color: 'tag--rojo' },
    { id: 'excelente', label: 'Excelente', color: 'tag--verde' },
  ];

  constructor(private svc: AgronomoService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa') || lista[0];
        if (activa) { this.temporadaId.set(activa.id); this.cargar(activa.id); }
        else this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cargar(id: string) {
    this.cargando.set(true); this.temporadaId.set(id);
    this.svc.listarEvaluaciones(id).subscribe({
      next: (r) => { this.evaluaciones.set(r.evaluaciones || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }

  abrirForm() {
    this.form = {
      fecha: new Date().toISOString().split('T')[0],
      estado_general: 'bueno', humedad_suelo: '',
      temperatura_campo: '', ndvi: '', observaciones: '',
    };
    this.errorForm.set(''); this.mostrarForm.set(true);
  }

  cerrarForm() { this.mostrarForm.set(false); this.errorForm.set(''); }

  guardar() {
    if (!this.form.fecha || !this.form.estado_general) {
      this.errorForm.set('Fecha y estado general son requeridos.'); return;
    }
    this.guardando.set(true);
    const datos: any = {
      fecha:             this.form.fecha,
      estado_general:    this.form.estado_general,
      observaciones:     this.form.observaciones || null,
    };
    if (this.form.humedad_suelo)     datos.humedad_suelo      = parseFloat(this.form.humedad_suelo);
    if (this.form.temperatura_campo) datos.temperatura_campo  = parseFloat(this.form.temperatura_campo);
    if (this.form.ndvi)              datos.ndvi               = parseFloat(this.form.ndvi);

    this.svc.registrarEvaluacion(this.temporadaId(), datos).subscribe({
      next: () => { this.guardando.set(false); this.cerrarForm(); this.cargar(this.temporadaId()); },
      error: (err) => { this.guardando.set(false); this.errorForm.set(err.error?.error || 'Error.'); }
    });
  }

  colorEstado(e: string): string {
    const s = this.estados.find(x => x.id === e);
    return s?.color || 'tag--gris';
  }
}