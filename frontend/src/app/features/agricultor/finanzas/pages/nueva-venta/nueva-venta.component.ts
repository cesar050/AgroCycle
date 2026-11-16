import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { FinanzasService } from '../../services/finanzas.service';
import { NotificacionService } from '../../../../../core/services/notificacion.service';

/**
 * CU-FIN-004 — Registrar Precio y Volumen de Venta.
 *
 * Página dedicada para registrar la cosecha vendida de una parcela
 * de la temporada. Resuelve el temporada_parcela_id real (y el
 * nombre de cada parcela) a partir del detalle de la temporada y
 * del catálogo de parcelas de la finca.
 */
@Component({
  selector: 'app-nueva-venta',
  standalone: true,
  imports: [CommonModule, DecimalPipe, FormsModule, RouterLink],
  templateUrl: './nueva-venta.component.html',
  styleUrl: './nueva-venta.component.scss',
})
export class NuevaVentaComponent implements OnInit {

  cargando        = signal(true);
  guardando       = signal(false);
  error           = signal('');

  temporadaId     = signal('');
  temporadaNombre = signal('');
  temporadaEstado = signal('');

  parcelas        = signal<any[]>([]);  // { tpId, nombre, superficie, estado }
  tpId            = signal('');

  form = {
    produccion_real_qq:        '',
    fecha_cosecha:             new Date().toISOString().split('T')[0],
    precio_venta_qq:           '',
    volumen_vendido_qq:        '',
    produccion_autoconsumo_qq: '',
  };

  constructor(
    private svc: FinanzasService,
    private router: Router,
    private route: ActivatedRoute,
    private notificacion: NotificacionService,
  ) {}

  ngOnInit() {
    const idParam = this.route.snapshot.queryParamMap.get('temporada');
    if (idParam) {
      this.temporadaId.set(idParam);
      this.cargarTemporada(idParam);
    } else {
      this.resolverTemporadaActiva();
    }
  }

  private resolverTemporadaActiva() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        const activa = lista.find((t: any) => t.estado === 'activa');
        const sel = activa || lista[0];
        if (sel) {
          this.temporadaId.set(sel.id);
          this.cargarTemporada(sel.id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  private cargarTemporada(id: string) {
    this.svc.obtenerTemporada(id).subscribe({
      next: (t) => {
        this.temporadaNombre.set(t?.nombre || '');
        this.temporadaEstado.set(t?.estado || '');
        const tps = t?.parcelas || [];
        if (t?.finca_id) {
          this.cargarNombresParcelas(t.finca_id, tps);
        } else {
          this.construirParcelas(tps, {});
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  /** Construye un mapa parcela_id -> {nombre, superficie} recorriendo los lotes de la finca. */
  private cargarNombresParcelas(fincaId: string, tps: any[]) {
    this.svc.listarLotes(fincaId).subscribe({
      next: (res) => {
        const lotes = res.lotes || res || [];
        if (!lotes.length) { this.construirParcelas(tps, {}); return; }

        const mapa: Record<string, any> = {};
        let pendientes = lotes.length;

        lotes.forEach((l: any) => {
          this.svc.listarParcelas(l.id).subscribe({
            next: (pr) => {
              const ps = pr.parcelas || pr || [];
              ps.forEach((p: any) => { mapa[p.id] = p; });
            },
            complete: () => {
              if (--pendientes === 0) this.construirParcelas(tps, mapa);
            },
            error: () => {
              if (--pendientes === 0) this.construirParcelas(tps, mapa);
            },
          });
        });
      },
      error: () => this.construirParcelas(tps, {}),
    });
  }

  private construirParcelas(tps: any[], mapa: Record<string, any>) {
    const items = tps.map((tp: any, i: number) => {
      const p = mapa[tp.parcela_id];
      return {
        tpId:       tp.id,
        nombre:     p?.nombre || `Parcela ${i + 1}`,
        superficie: p?.superficie_ha ?? null,
        estado:     tp.estado_fenologico || null,
      };
    });
    this.parcelas.set(items);
    if (items.length === 1) this.tpId.set(items[0].tpId);
    this.cargando.set(false);
  }

  seleccionarParcela(tpId: string) {
    this.tpId.set(tpId);
  }

  ingresos = computed(() => {
    const vol = parseFloat(this.form.volumen_vendido_qq) || 0;
    const precio = parseFloat(this.form.precio_venta_qq) || 0;
    return Math.round(vol * precio * 100) / 100;
  });

  autoconsumoSugerido = computed(() => {
    const prod = parseFloat(this.form.produccion_real_qq) || 0;
    const vend = parseFloat(this.form.volumen_vendido_qq) || 0;
    const r = Math.round((prod - vend) * 100) / 100;
    return r > 0 ? r : 0;
  });

  get excedeProduccion(): boolean {
    const prod = parseFloat(this.form.produccion_real_qq) || 0;
    const vend = parseFloat(this.form.volumen_vendido_qq) || 0;
    return vend > prod && prod > 0;
  }

  get puedeGuardar(): boolean {
    return !!this.tpId() &&
           !!this.form.produccion_real_qq &&
           !!this.form.fecha_cosecha &&
           !!this.form.precio_venta_qq &&
           !!this.form.volumen_vendido_qq &&
           !this.excedeProduccion;
  }

  guardar() {
    if (!this.tpId()) {
      this.error.set('Selecciona la parcela cosechada.');
      return;
    }
    if (this.excedeProduccion) {
      this.error.set('El volumen vendido no puede superar la producción real.');
      return;
    }
    if (!this.puedeGuardar) {
      this.error.set('Completa producción, fecha, precio y volumen vendido.');
      return;
    }

    this.guardando.set(true);
    this.error.set('');

    const datos = {
      produccion_real_qq:        parseFloat(this.form.produccion_real_qq),
      fecha_cosecha:             this.form.fecha_cosecha,
      precio_venta_qq:           parseFloat(this.form.precio_venta_qq),
      volumen_vendido_qq:        parseFloat(this.form.volumen_vendido_qq),
      produccion_autoconsumo_qq: this.form.produccion_autoconsumo_qq
        ? parseFloat(this.form.produccion_autoconsumo_qq) : null,
    };

    this.svc.registrarVenta(this.tpId(), datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.notificacion.exito('Venta registrada correctamente.');
        this.router.navigate(['/app/finanzas'], {
          queryParams: { temporada: this.temporadaId() },
        });
      },
      error: (err) => {
        this.guardando.set(false);
        const mensaje = err.error?.error || 'No se pudo registrar la venta.';
        this.error.set(mensaje);
        this.notificacion.error(mensaje);
      },
    });
  }
}
