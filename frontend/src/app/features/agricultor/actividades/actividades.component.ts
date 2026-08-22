import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ActividadesService } from './services/actividades.service';

@Component({
  selector: 'app-actividades',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, DecimalPipe],
  templateUrl: './actividades.component.html',
  styleUrl: './actividades.component.scss'
})
export class ActividadesComponent implements OnInit {
  protected readonly String = String;

  cargando       = signal(true);
  guardando      = signal(false);
  mostrarFormulario = signal(false);
  error          = signal('');
  errorForm      = signal('');

  temporadas     = signal<any[]>([]);
  temporadaId    = signal('');
  actividades    = signal<any[]>([]);

  // Filtros
  filtroTipo     = signal('');
  filtroFecha    = signal('');

  // Formulario
  form = {
    tipo_actividad_id: '',
    fecha:             '',
    descripcion:       '',
    costo_total:       '',
    observaciones:     '',
    // Riego
    tipo_riego:        '',
    duracion_horas:    '',
    // Fertilización
    producto:          '',
    cantidad_kg:       '',
    // Fitosanitario
    plaga_enfermedad:  '',
    producto_aplicado: '',
  };

  tiposActividad = [
    { id: 1, nombre: 'Preparación del terreno', icono: 'terrain' },
    { id: 2, nombre: 'Siembra',                  icono: 'seed' },
    { id: 3, nombre: 'Fertilización',             icono: 'fertilizer' },
    { id: 4, nombre: 'Control fitosanitario',     icono: 'pest' },
    { id: 5, nombre: 'Riego',                     icono: 'water' },
    { id: 6, nombre: 'Mano de obra',              icono: 'labor' },
    { id: 7, nombre: 'Cosecha',                   icono: 'harvest' },
    { id: 8, nombre: 'Monitoreo',                 icono: 'monitor' },
    { id: 9, nombre: 'Otro',                      icono: 'other' },
  ];

  tiposRiego = ['Goteo', 'Aspersión', 'Gravedad', 'Manual'];

  constructor(private svc: ActividadesService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa');
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarActividades(activa.id);
        } else if (lista.length > 0) {
          this.temporadaId.set(lista[0].id);
          this.cargarActividades(lista[0].id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarActividades(temporadaId: string) {
    this.cargando.set(true);
    this.svc.listarPorTemporada(temporadaId).subscribe({
      next: (res) => {
        this.actividades.set(res.actividades || res || []);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cambiarTemporada(id: string) {
    this.temporadaId.set(id);
    this.cargarActividades(id);
  }

  get actividadesFiltradas(): any[] {
    return this.actividades().filter(a => {
      const okTipo  = !this.filtroTipo() ||
        String(a.tipo_actividad_id) === this.filtroTipo();
      const okFecha = !this.filtroFecha() ||
        a.fecha?.startsWith(this.filtroFecha());
      return okTipo && okFecha;
    });
  }

  get totalCosto(): number {
    return this.actividadesFiltradas.reduce(
      (s, a) => s + (parseFloat(a.costo_total) || 0), 0
    );
  }

  get tipoSeleccionado(): number {
    return parseInt(this.form.tipo_actividad_id) || 0;
  }

  abrirFormulario() {
    this.form = {
      tipo_actividad_id: '',
      fecha:             new Date().toISOString().split('T')[0],
      descripcion:       '',
      costo_total:       '',
      observaciones:     '',
      tipo_riego:        '',
      duracion_horas:    '',
      producto:          '',
      cantidad_kg:       '',
      plaga_enfermedad:  '',
      producto_aplicado: '',
    };
    this.errorForm.set('');
    this.mostrarFormulario.set(true);
  }

  cerrarFormulario() {
    this.mostrarFormulario.set(false);
    this.errorForm.set('');
  }

  guardar() {
    if (!this.form.tipo_actividad_id || !this.form.fecha) {
      this.errorForm.set('Tipo de actividad y fecha son requeridos.');
      return;
    }

    this.guardando.set(true);
    this.errorForm.set('');

    const datos: any = {
      tipo_actividad_id: parseInt(this.form.tipo_actividad_id),
      fecha:             this.form.fecha,
      descripcion:       this.form.descripcion || null,
      costo_total:       parseFloat(this.form.costo_total) || 0,
      observaciones:     this.form.observaciones || null,
    };

    // Campos adicionales según tipo
    if (this.tipoSeleccionado === 5) { // Riego
      datos.tipo_riego    = this.form.tipo_riego || null;
      datos.duracion_horas = parseFloat(this.form.duracion_horas) || null;
    }

    if (this.tipoSeleccionado === 3) { // Fertilización
      datos.producto    = this.form.producto || null;
      datos.cantidad_kg = parseFloat(this.form.cantidad_kg) || null;
    }

    if (this.tipoSeleccionado === 4) { // Fitosanitario
      datos.plaga_enfermedad  = this.form.plaga_enfermedad || null;
      datos.producto_aplicado = this.form.producto_aplicado || null;
    }

    this.svc.registrar(this.temporadaId(), datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.cerrarFormulario();
        this.cargarActividades(this.temporadaId());
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorForm.set(
          err.error?.error || 'Error al registrar la actividad.'
        );
      }
    });
  }

  confirmarEliminar(actividad: any) {
    if (!confirm(
      `¿Eliminar la actividad "${this.nombreTipo(actividad.tipo_actividad_id)}" del ${actividad.fecha}?`
    )) return;

    this.svc.eliminar(actividad.id).subscribe({
      next: () => this.cargarActividades(this.temporadaId()),
      error: () => {},
    });
  }

  nombreTipo(id: number): string {
    return this.tiposActividad.find(t => t.id === id)?.nombre || 'Actividad';
  }

  colorTipo(id: number): string {
    const colores: Record<number, string> = {
      1: '#795548', 2: '#4CAF50', 3: '#2196F3',
      4: '#F44336', 5: '#03A9F4', 6: '#FF9800',
      7: '#FFC107', 8: '#9C27B0', 9: '#607D8B',
    };
    return colores[id] || '#607D8B';
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }
}