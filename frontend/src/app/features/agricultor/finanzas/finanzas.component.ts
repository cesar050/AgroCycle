import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { FinanzasService } from './services/finanzas.service';
import { NotificacionService } from '../../../core/services/notificacion.service';

/**
 * Vista principal del módulo Financiero (AC-FIN).
 *
 * Balance tabular de la temporada:
 *  - Resultado financiero (ingresos, costos, utilidad, margen, costo/qq)
 *  - Gastos por categoría (CU-FIN-003)
 *  - Detalle de gastos
 *  - Comparativo entre temporadas (CU-FIN-007)
 *
 * El registro de costos (CU-FIN-002) y de ventas (CU-FIN-004) vive
 * ahora en páginas dedicadas (/app/finanzas/nuevo-costo y
 * /app/finanzas/nueva-venta), no en modales.
 */
@Component({
  selector: 'app-finanzas',
  standalone: true,
  imports: [CommonModule, DecimalPipe, RouterLink],
  templateUrl: './finanzas.component.html',
  styleUrl: './finanzas.component.scss',
})
export class FinanzasComponent implements OnInit {

  cargando     = signal(true);
  error        = signal('');

  temporadas   = signal<any[]>([]);
  temporadaId  = signal('');
  gastos       = signal<any[]>([]);
  rentabilidad = signal<any>(null);

  comparativo  = signal<any>(null);

  categorias = [
    { id: 'semillas',      label: 'Semillas' },
    { id: 'fertilizantes', label: 'Fertilizantes' },
    { id: 'agroquimicos',  label: 'Agroquímicos' },
    { id: 'mano_obra',     label: 'Mano de obra' },
    { id: 'otros',         label: 'Otros' },
  ];

  constructor(
    private svc: FinanzasService,
    private route: ActivatedRoute,
    private notificacion: NotificacionService,
  ) {}

  ngOnInit() {
    this.cargarTemporadas();
    this.cargarComparativo();
  }

  cargarTemporadas() {
    const preferida = this.route.snapshot.queryParamMap.get('temporada');
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const porParam = preferida
          ? lista.find((t: any) => t.id === preferida) : null;
        const activa = lista.find((t: any) => t.estado === 'activa');
        const sel = porParam || activa || lista[0];
        if (sel) {
          this.cargarDatos(sel.id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => {
        this.error.set('No se pudieron cargar las temporadas.');
        this.cargando.set(false);
      },
    });
  }

  cargarDatos(temporadaId: string) {
    this.cargando.set(true);
    this.temporadaId.set(temporadaId);

    this.svc.listarGastos(temporadaId).subscribe({
      next: (res) => this.gastos.set(res.compras || res.gastos || []),
      error: () => this.gastos.set([]),
    });

    this.svc.calcularRentabilidad(temporadaId).subscribe({
      next: (res) => {
        this.rentabilidad.set(res);
        this.cargando.set(false);
      },
      error: () => {
        this.rentabilidad.set(null);
        this.cargando.set(false);
      },
    });
  }

  cargarComparativo() {
    this.svc.compararTemporadas().subscribe({
      next: (res) => this.comparativo.set(res),
      error: () => this.comparativo.set(null),
    });
  }

  confirmarEliminarCompra(compra: any) {
    if (!confirm(`¿Eliminar el gasto de $${compra.costo_total}?`)) return;
    this.svc.eliminarCompra(compra.id).subscribe({
      next: () => {
        this.notificacion.exito('Gasto eliminado correctamente.');
        this.cargarDatos(this.temporadaId());
        this.cargarComparativo();
      },
      error: (err) => this.notificacion.errorHttp(err, 'No se pudo eliminar el gasto.'),
    });
  }

  labelCategoria(cat: string): string {
    return this.categorias.find(c => c.id === cat)?.label || cat;
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }

  // --- Derivados del resultado financiero ---
  get resultado(): any { return this.rentabilidad()?.resultado || null; }
  get gananciaNeta(): number { return this.resultado?.ganancia_neta ?? 0; }
  get hayUtilidad(): boolean { return this.gananciaNeta >= 0; }
  get totalGastos(): number { return this.rentabilidad()?.gastos?.total ?? 0; }
  get totalIngresos(): number { return this.rentabilidad()?.ingresos?.total ?? 0; }

  pctCategoria(valor: number): number {
    const total = this.totalGastos;
    return total > 0 ? (valor / total) * 100 : 0;
  }

  // --- Comparativo entre temporadas (CU-FIN-007) ---
  get comparativoTemporadas(): any[] {
    return this.comparativo()?.temporadas || [];
  }

  maxAbsGanancia = computed(() => {
    const temps = this.comparativo()?.temporadas || [];
    const vals = temps
      .map((t: any) => Math.abs(t.ganancia_neta ?? 0))
      .filter((v: number) => v > 0);
    return vals.length ? Math.max(...vals) : 1;
  });

  anchoBarra(ganancia: number | null): number {
    if (ganancia == null) return 0;
    return Math.min(100, (Math.abs(ganancia) / this.maxAbsGanancia()) * 100);
  }
}
