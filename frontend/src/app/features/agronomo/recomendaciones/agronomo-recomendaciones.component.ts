import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgronomoService } from '../services/agronomo.service';

@Component({
  selector: 'app-agronomo-recomendaciones',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agronomo-recomendaciones.component.html',
  styleUrl: './agronomo-recomendaciones.component.scss'
})
export class AgronomoRecomendacionesComponent implements OnInit {

  cargando        = signal(true);
  guardando       = signal(false);
  mostrarForm     = signal(false);
  errorForm       = signal('');

  temporadas      = signal<any[]>([]);
  temporadaId     = signal('');
  recomendaciones = signal<any[]>([]);

  form = {
    tipo:              '',
    descripcion:       '',
    urgencia:          'baja',
    accion_recomendada: '',
    fecha_limite:      '',
  };

  tipos     = ['Fertilización','Riego','Fitosanitario','Cosecha','Siembra','Monitoreo','Otro'];
  urgencias = [
    { id: 'baja',  label: 'Baja' },
    { id: 'media', label: 'Media' },
    { id: 'alta',  label: 'Alta' },
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
    this.svc.listarRecomendaciones(id).subscribe({
      next: (r) => { this.recomendaciones.set(r.recomendaciones || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }

  abrirForm() {
    this.form = { tipo: '', descripcion: '', urgencia: 'baja', accion_recomendada: '', fecha_limite: '' };
    this.errorForm.set(''); this.mostrarForm.set(true);
  }

  cerrarForm() { this.mostrarForm.set(false); this.errorForm.set(''); }

  guardar() {
    if (!this.form.tipo || !this.form.descripcion) {
      this.errorForm.set('Tipo y descripción son requeridos.'); return;
    }
    this.guardando.set(true);
    this.svc.registrarRecomendacion(this.temporadaId(), {
      tipo:               this.form.tipo,
      descripcion:        this.form.descripcion,
      urgencia:           this.form.urgencia,
      accion_recomendada: this.form.accion_recomendada || null,
      fecha_limite:       this.form.fecha_limite || null,
    }).subscribe({
      next: () => { this.guardando.set(false); this.cerrarForm(); this.cargar(this.temporadaId()); },
      error: (err) => { this.guardando.set(false); this.errorForm.set(err.error?.error || 'Error.'); }
    });
  }

  colorU(u: string): string {
    if (u === 'alta')  return 'tag--rojo';
    if (u === 'media') return 'tag--naranja';
    return 'tag--verde';
  }
}