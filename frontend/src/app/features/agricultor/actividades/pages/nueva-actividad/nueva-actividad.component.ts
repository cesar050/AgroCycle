import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ActividadesService } from '../../services/actividades.service';

@Component({
  selector: 'app-nueva-actividad',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './nueva-actividad.component.html',
  styleUrl: './nueva-actividad.component.scss'
})
export class NuevaActividadComponent implements OnInit {

  cargando = signal(false);
  error    = signal('');

  temporadas  = signal<any[]>([]);
  parcelas    = signal<any[]>([]);
  tipos       = signal<any[]>([]);

  temporadaId = '';

  form = {
    temporada_parcela_id: '',
    tipo_actividad_id:    '',
    fecha:                '',
    descripcion:          '',
    costo_total:          '',
    observaciones:        '',
    // Riego (5)
    tipo_riego:                 '',
    duracion_horas:             '',
    porcentaje_parcela_regada:  '100',
    // Fertilizacion (3)
    insumo_personalizado:  '',
    dosis_kg_ha:           '',
    metodo_aplicacion:     '',
    costo_unitario:        '',
    // Control fitosanitario (4)
    tipo_control:                   '',
    dosis_aplicada:                 '',
    motivo:                         '',
    incidencia_porcentaje:          '',
    condicion_humedad_momento:      '',
    condicion_temperatura_momento:  '',
    efectividad_observada:          '',
    // Mano de obra (6)
    tipo_labor:          '',
    numero_personas:     '1',
    dias_trabajados:     '',
    costo_jornal:        '',
    es_mano_obra_propia: false,
  };

  // Catalogo fallback (ids alineados con el backend)
  readonly tiposFallback = [
    { id: 1, nombre: 'Preparación del terreno' },
    { id: 2, nombre: 'Siembra' },
    { id: 3, nombre: 'Fertilización' },
    { id: 4, nombre: 'Control fitosanitario' },
    { id: 5, nombre: 'Riego' },
    { id: 6, nombre: 'Mano de obra' },
    { id: 7, nombre: 'Cosecha' },
    { id: 8, nombre: 'Monitoreo' },
    { id: 9, nombre: 'Otro' },
  ];

  readonly tiposRiego = [
    { value: 'perdido',   label: 'Gravedad / perdido' },
    { value: 'aspersion', label: 'Aspersión' },
    { value: 'goteo',     label: 'Goteo' },
  ];

  readonly tiposControl = ['preventivo', 'curativo', 'biologico'];
  readonly efectividades = ['alta', 'media', 'baja', 'nula'];

  constructor(
    private svc: ActividadesService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.form.fecha = new Date().toISOString().split('T')[0];
    this.cargarTemporadas();
    this.cargarTipos();
  }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const preId = this.route.snapshot.queryParamMap.get('temporada');
        const activa = lista.find((t: any) => t.estado === 'activa');
        const elegida = preId || activa?.id || lista[0]?.id;
        if (elegida) { this.temporadaId = elegida; this.cargarParcelas(elegida); }
      },
      error: () => {}
    });
  }

  cargarParcelas(temporadaId: string) {
    this.temporadaId = temporadaId;
    this.parcelas.set([]);
    this.form.temporada_parcela_id = '';
    if (!temporadaId) return;
    this.svc.obtenerTemporada(temporadaId).subscribe({
      next: (res) => {
        const ps = res.parcelas || [];
        this.parcelas.set(ps);
        // Llegada desde Mapa General (?parcela=<parcela_id>, no el id de
        // temporada_parcelas): preseleccionar la fila cuyo parcela_id
        // coincida con la parcela elegida en el mapa.
        const parcelaIdPre = this.route.snapshot.queryParamMap.get('parcela');
        const match = parcelaIdPre ? ps.find((p: any) => p.parcela_id === parcelaIdPre) : null;
        if (match) this.form.temporada_parcela_id = match.id;
        else if (ps.length === 1) this.form.temporada_parcela_id = ps[0].id;
      },
      error: () => {}
    });
  }

  cargarTipos() {
    this.svc.listarTipos().subscribe({
      next: (res) => {
        const lista = res.tipos || [];
        this.tipos.set(lista.length ? lista : this.tiposFallback);
      },
      error: () => this.tipos.set(this.tiposFallback),
    });
  }

  get tipoSel(): number {
    return parseInt(this.form.tipo_actividad_id) || 0;
  }

  parcelaRef(p: any): string {
    const pid = p?.parcela_id || '';
    return pid ? '#' + String(pid).slice(0, 8).toUpperCase() : 'Parcela';
  }

  get puedeGuardar(): boolean {
    return !!this.temporadaId &&
           !!this.form.temporada_parcela_id &&
           !!this.form.tipo_actividad_id &&
           !!this.form.fecha;
  }

  private num(v: string): number | null {
    const n = parseFloat(v);
    return isNaN(n) ? null : n;
  }

  guardar() {
    if (!this.puedeGuardar) {
      this.error.set('Temporada, parcela, tipo de actividad y fecha son obligatorios.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    const f = this.form;
    const parcela = this.parcelas().find(p => p.id === f.temporada_parcela_id);

    const datos: any = {
      temporada_parcela_id: f.temporada_parcela_id,
      parcela_id:           parcela?.parcela_id || null,
      tipo_actividad_id:    parseInt(f.tipo_actividad_id),
      fecha:                f.fecha,
      descripcion:          f.descripcion.trim() || null,
      observaciones:        f.observaciones.trim() || null,
      costo_total:          this.num(f.costo_total) || 0,
    };

    if (this.tipoSel === 5) {
      datos.tipo_riego = f.tipo_riego || null;
      datos.duracion_horas = this.num(f.duracion_horas);
      datos.porcentaje_parcela_regada = this.num(f.porcentaje_parcela_regada) ?? 100;
    } else if (this.tipoSel === 3) {
      datos.insumo_personalizado = f.insumo_personalizado.trim() || null;
      datos.dosis_kg_ha = this.num(f.dosis_kg_ha);
      datos.metodo_aplicacion = f.metodo_aplicacion.trim() || null;
      datos.costo_unitario = this.num(f.costo_unitario);
    } else if (this.tipoSel === 4) {
      datos.tipo_control = f.tipo_control || null;
      datos.dosis_aplicada = this.num(f.dosis_aplicada);
      datos.metodo_aplicacion = f.metodo_aplicacion.trim() || null;
      datos.motivo = f.motivo.trim() || null;
      datos.incidencia_porcentaje = this.num(f.incidencia_porcentaje);
      datos.condicion_humedad_momento = this.num(f.condicion_humedad_momento);
      datos.condicion_temperatura_momento = this.num(f.condicion_temperatura_momento);
      datos.efectividad_observada = f.efectividad_observada || null;
    } else if (this.tipoSel === 6) {
      datos.tipo_labor = f.tipo_labor.trim() || null;
      datos.numero_personas = this.num(f.numero_personas) ?? 1;
      datos.dias_trabajados = this.num(f.dias_trabajados);
      datos.costo_jornal = this.num(f.costo_jornal);
      datos.es_mano_obra_propia = !!f.es_mano_obra_propia;
    }

    this.svc.registrar(this.temporadaId, datos).subscribe({
      next: () => {
        this.cargando.set(false);
        this.router.navigate(['/app/actividades']);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'No se pudo registrar la actividad.');
      }
    });
  }
}
