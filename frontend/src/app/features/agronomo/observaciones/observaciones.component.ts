import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgronomoService } from '../services/agronomo.service';

@Component({
  selector: 'app-observaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './observaciones.component.html',
  styleUrl: './observaciones.component.scss'
})
export class ObservacionesComponent implements OnInit {

  cargando      = signal(true);
  guardando     = signal(false);
  mostrarForm   = signal(false);
  error         = signal('');
  errorForm     = signal('');

  temporadas    = signal<any[]>([]);
  temporadaId   = signal('');
  observaciones = signal<any[]>([]);

  form = {
    tipo:        '',
    descripcion: '',
    fecha:       '',
    severidad:   'normal',
  };

  tipos = [
    'Estado del cultivo', 'Plagas y enfermedades', 'Deficiencias nutricionales',
    'Estrés hídrico', 'Condiciones del suelo', 'Daño climático', 'Otro',
  ];

  severidades = [
    { id: 'normal',   label: 'Normal' },
    { id: 'alerta',   label: 'Alerta' },
    { id: 'critico',  label: 'Crítico' },
  ];

  constructor(private svc: AgronomoService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa') || lista[0];
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarObservaciones(activa.id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarObservaciones(id: string) {
    this.cargando.set(true);
    this.temporadaId.set(id);
    this.svc.listarObservaciones(id).subscribe({
      next: (r) => { this.observaciones.set(r.observaciones || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }

  abrirForm() {
    this.form = {
      tipo: '', descripcion: '',
      fecha: new Date().toISOString().split('T')[0], severidad: 'normal',
    };
    this.errorForm.set('');
    this.mostrarForm.set(true);
  }

  cerrarForm() { this.mostrarForm.set(false); this.errorForm.set(''); }

  guardar() {
    if (!this.form.tipo || !this.form.descripcion || !this.form.fecha) {
      this.errorForm.set('Tipo, descripción y fecha son requeridos.');
      return;
    }
    this.guardando.set(true);
    this.svc.registrarObservacion(this.temporadaId(), {
      tipo: this.form.tipo,
      descripcion: this.form.descripcion,
      fecha: this.form.fecha,
      severidad: this.form.severidad,
    }).subscribe({
      next: () => {
        this.guardando.set(false);
        this.cerrarForm();
        this.cargarObservaciones(this.temporadaId());
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorForm.set(err.error?.error || 'Error al guardar.');
      }
    });
  }

  colorSeveridad(s: string): string {
    if (s === 'critico') return 'tag--rojo';
    if (s === 'alerta')  return 'tag--naranja';
    return 'tag--gris';
  }
}