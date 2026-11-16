import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { TemporadaService } from '../../services/temporada.service';
import { NotificacionService } from '../../../../../core/services/notificacion.service';

interface FenoEtapa { key: string; label: string; }

@Component({
  selector: 'app-detalle-temporada',
  standalone: true,
  imports: [CommonModule, RouterLink, DecimalPipe],
  templateUrl: './detalle-temporada.component.html',
  styleUrl: './detalle-temporada.component.scss'
})
export class DetalleTemporadaComponent implements OnInit {

  id = '';

  cargando               = signal(true);
  error                  = signal('');
  temporada              = signal<any>(null);
  estimaciones           = signal<any[]>([]);
  produccionEstimadaTotal = signal<number | null>(null);
  actualizandoFenologia  = signal(false);
  generando              = signal<Set<string>>(new Set());

  // Etapas fenologicas canonicas del backend (orden del ciclo del maiz)
  readonly etapas: FenoEtapa[] = [
    { key: 'emergencia',             label: 'Emergencia' },
    { key: 'crecimiento_vegetativo', label: 'Crecimiento' },
    { key: 'floracion',              label: 'Floración' },
    { key: 'llenado_grano',          label: 'Llenado grano' },
    { key: 'maduracion',             label: 'Maduración' },
    { key: 'cosecha',                label: 'Cosecha' },
  ];

  private readonly cultivos: Record<number, string> = { 1: 'Maíz' };

  esActiva = computed(() => this.temporada()?.estado === 'activa');

  constructor(
    private route: ActivatedRoute,
    private svc: TemporadaService,
    private notificacion: NotificacionService,
  ) {}

  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get('id') || '';
    this.cargar();
  }

  cargar() {
    this.cargando.set(true);
    this.svc.obtener(this.id).subscribe({
      next: (res) => { this.temporada.set(res); this.cargando.set(false); },
      error: (err) => {
        this.error.set(err.error?.error || 'No se pudo cargar la temporada.');
        this.cargando.set(false);
      }
    });
    this.cargarEstimaciones();
  }

  cargarEstimaciones() {
    this.svc.obtenerEstimaciones(this.id).subscribe({
      next: (res) => {
        this.estimaciones.set(res.parcelas || []);
        this.produccionEstimadaTotal.set(res.produccion_total_estimada_qq ?? null);
      },
      error: () => {}
    });
  }

  // ---- Datos derivados ----
  get parcelas(): any[] { return this.temporada()?.parcelas || []; }

  get totalParcelas(): number { return this.parcelas.length; }

  get avancePromedio(): number {
    const ps = this.parcelas;
    if (!ps.length) return 0;
    const sum = ps.reduce((s, p) => s + (p.avance_ciclo_porcentaje || 0), 0);
    return Math.round(sum / ps.length);
  }

  get parcelasCosechadas(): number {
    return this.parcelas.filter(p => p.estado_fenologico === 'cosecha').length;
  }

  estimacionDeParcela(tpId: string): any {
    return this.estimaciones().find(e => e.temporada_parcela_id === tpId) || null;
  }

  etapaIndex(estado: string): number {
    return this.etapas.findIndex(e => e.key === estado);
  }

  avanceParcela(p: any): number {
    const v = p?.avance_ciclo_porcentaje;
    return v != null ? Math.min(Math.round(v), 100) : 0;
  }

  cultivoNombre(id: number): string { return this.cultivos[id] || 'Cultivo'; }

  labelEstado(estado: string): string {
    const map: Record<string, string> = {
      activa: 'Activa', cerrada: 'Cerrada',
      cancelada: 'Cancelada', pausada: 'Pausada'
    };
    return map[estado] || estado;
  }

  tagEstado(estado: string): string {
    const map: Record<string, string> = {
      activa: 'tag--verde', cerrada: 'tag--gris',
      cancelada: 'tag--rojo', pausada: 'tag--naranja'
    };
    return map[estado] || 'tag--gris';
  }

  etapaLabel(estado: string): string {
    return this.etapas.find(e => e.key === estado)?.label || estado || '—';
  }

  parcelaRef(p: any): string {
    const pid = p?.parcela_id || '';
    return pid ? pid.slice(0, 8).toUpperCase() : '—';
  }

  estaCosechada(p: any): boolean {
    return p?.estado_fenologico === 'cosecha';
  }

  generandoDe(tpId: string): boolean {
    return this.generando().has(tpId);
  }

  // ---- Acciones ----
  actualizarFenologia() {
    this.actualizandoFenologia.set(true);
    this.svc.actualizarFenologia(this.id).subscribe({
      next: () => {
        this.actualizandoFenologia.set(false);
        this.notificacion.exito('Fenología actualizada correctamente.');
        this.cargar();
      },
      error: (err) => {
        this.actualizandoFenologia.set(false);
        this.notificacion.errorHttp(err, 'No se pudo actualizar la fenología.');
      }
    });
  }

  generarEstimacion(tpId: string) {
    this.generando.update(s => { const n = new Set(s); n.add(tpId); return n; });
    this.svc.generarEstimacion(tpId).subscribe({
      next: () => {
        this.generando.update(s => { const n = new Set(s); n.delete(tpId); return n; });
        this.notificacion.exito('Estimación de producción generada correctamente.');
        this.cargarEstimaciones();
      },
      error: (err) => {
        this.generando.update(s => { const n = new Set(s); n.delete(tpId); return n; });
        this.notificacion.errorHttp(err, 'No se pudo generar la estimación.');
      }
    });
  }
}
