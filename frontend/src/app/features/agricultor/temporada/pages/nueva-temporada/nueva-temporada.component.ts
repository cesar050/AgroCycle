import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TemporadaService } from '../../services/temporada.service';
import { ApiService } from '../../../../../core/services/api.service';

@Component({
  selector: 'app-nueva-temporada',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './nueva-temporada.component.html',
  styleUrl: './nueva-temporada.component.scss'
})
export class NuevaTemporadaComponent implements OnInit {

  // Formulario
  nombre          = '';
  fincaId         = '';
  cultivoId       = '1'; // Maíz por defecto
  fechaInicio     = '';
  fechaFinEstimada = '';
  observaciones   = '';

  // Estado
  cargando  = signal(false);
  error     = signal('');
  paso      = signal<1|2>(1);

  // Datos del formulario
  fincas   = signal<any[]>([]);
  lotes    = signal<any[]>([]);
  parcelas = signal<any[]>([]);

  // Selección de parcelas
  parcelasSeleccionadas = signal<Set<string>>(new Set());

  cultivos = [
    { id: 1, nombre: 'Maíz' },
  ];

  variedades: Record<number, {id: number; nombre: string}[]> = {
    1: [
      { id: 1, nombre: 'INIAP-101' },
      { id: 2, nombre: 'INIAP-122' },
      { id: 3, nombre: 'DK-7088' },
      { id: 4, nombre: 'Pioneer 30F35' },
      { id: 5, nombre: 'Criolla local' },
      { id: 6, nombre: 'Triunfo NB-7253' },
    ]
  };

  variedadId      = '';
  densidadSiembra = '';

  // Temporada creada (para paso 2)
  temporadaCreada = signal<any>(null);

  constructor(
    private svc: TemporadaService,
    private router: Router,
  ) {}

  ngOnInit() { this.cargarFincas(); }

  cargarFincas() {
    this.svc.listarFincas().subscribe({
      next: (res) => {
        const lista = Array.isArray(res) ? res : (res.fincas || []);
        this.fincas.set(lista);
        if (lista.length === 1) {
          this.fincaId = lista[0].id;
          this.cargarLotes(lista[0].id);
        }
      },
      error: () => {}
    });
  }

  cargarLotes(fincaId: string) {
    this.fincaId = fincaId;
    this.lotes.set([]);
    this.parcelas.set([]);
    this.svc.listarLotes(fincaId).subscribe({
      next: (res) => {
        const lista = res.lotes || res || [];
        this.lotes.set(lista);
        // Cargar parcelas de todos los lotes
        lista.forEach((l: any) => this.cargarParcelasDeLote(l.id));
      },
      error: () => {}
    });
  }

  cargarParcelasDeLote(loteId: string) {
    this.svc.listarParcelas(loteId).subscribe({
      next: (res) => {
        const nuevas = res.parcelas || res || [];
        this.parcelas.update(prev => [...prev, ...nuevas]);
      },
      error: () => {}
    });
  }

  toggleParcela(parcelaId: string) {
    this.parcelasSeleccionadas.update(set => {
      const nuevo = new Set(set);
      if (nuevo.has(parcelaId)) nuevo.delete(parcelaId);
      else nuevo.add(parcelaId);
      return nuevo;
    });
  }

  estaSeleccionada(id: string): boolean {
    return this.parcelasSeleccionadas().has(id);
  }

  get parcelasArray(): string[] {
    return Array.from(this.parcelasSeleccionadas());
  }

  get puedeGuardarPaso1(): boolean {
    return !!this.nombre.trim() &&
           !!this.fincaId &&
           !!this.cultivoId &&
           !!this.fechaInicio &&
           this.parcelasSeleccionadas().size > 0;
  }

  guardarPaso1() {
    if (!this.puedeGuardarPaso1) {
      this.error.set(
        'Completa todos los campos requeridos y selecciona al menos una parcela.'
      );
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    const datos = {
      finca_id:          this.fincaId,
      cultivo_id:        parseInt(this.cultivoId),
      nombre:            this.nombre.trim(),
      fecha_inicio:      this.fechaInicio,
      fecha_fin_estimada: this.fechaFinEstimada || null,
      observaciones:     this.observaciones.trim() || null,
    };

    this.svc.registrar(datos).subscribe({
      next: (res) => {
        this.temporadaCreada.set(res);
        // Vincular parcelas
        this.vincularParcelas(res.id || res.temporada_id);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'Error al crear la temporada.');
      }
    });
  }

  vincularParcelas(temporadaId: string) {
    const promesas = this.parcelasArray.map(parcelaId =>
      this.svc.vincularParcela(temporadaId, {
        parcela_id:       parcelaId,
        variedad_semilla_id: this.variedadId
          ? parseInt(this.variedadId) : null,
        densidad_siembra_kg_ha: this.densidadSiembra
          ? parseFloat(this.densidadSiembra) : null,
        fecha_siembra: this.fechaInicio,
      }).toPromise()
    );

    Promise.allSettled(promesas).then(() => {
      this.cargando.set(false);
      this.router.navigate(['/app/temporada']);
    });
  }

  generarNombre() {
    if (this.fechaInicio) {
      const anio = new Date(this.fechaInicio).getFullYear();
      const cultivo = this.cultivos.find(
        c => c.id === parseInt(this.cultivoId)
      )?.nombre || 'Cultivo';
      this.nombre = `Temporada ${cultivo} ${anio}-${anio + 1}`;
    }
  }
}