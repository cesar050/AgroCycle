import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, Router, ActivatedRoute } from '@angular/router';
import { FinanzasService } from '../../services/finanzas.service';

/**
 * CU-FIN-002 — Registrar Compra e Insumo.
 *
 * Página dedicada y amplia para registrar un gasto/compra de la
 * temporada. Reemplaza al antiguo modal: formularios complejos van
 * en su propia ruta, no en un overlay.
 */
@Component({
  selector: 'app-nuevo-costo',
  standalone: true,
  imports: [CommonModule, DecimalPipe, FormsModule, RouterLink],
  templateUrl: './nuevo-costo.component.html',
  styleUrl: './nuevo-costo.component.scss',
})
export class NuevoCostoComponent implements OnInit {

  cargando        = signal(true);
  guardando       = signal(false);
  error           = signal('');

  temporadaId     = signal('');
  temporadaNombre = signal('');
  temporadaEstado = signal('');

  // Solo las categorías que acepta el backend (CHECK de la tabla compras).
  categorias = [
    { id: 'semillas',      label: 'Semillas' },
    { id: 'fertilizantes', label: 'Fertilizantes' },
    { id: 'agroquimicos',  label: 'Agroquímicos' },
    { id: 'mano_obra',     label: 'Mano de obra' },
    { id: 'otros',         label: 'Otros' },
  ];

  unidades = ['kg', 'g', 'L', 'mL', 'unidad', 'saco', 'quintal', 'jornal'];

  form = {
    categoria:              '',
    producto_personalizado: '',
    cantidad:               '',
    unidad_medida:          'kg',
    precio_unitario:        '',
    fecha_compra:           new Date().toISOString().split('T')[0],
    proveedor:              '',
  };

  constructor(
    private svc: FinanzasService,
    private router: Router,
    private route: ActivatedRoute,
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

  private cargarTemporada(id: string) {
    this.svc.obtenerTemporada(id).subscribe({
      next: (t) => {
        this.temporadaNombre.set(t?.nombre || '');
        this.temporadaEstado.set(t?.estado || '');
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  private resolverTemporadaActiva() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        const activa = lista.find((t: any) => t.estado === 'activa');
        const sel = activa || lista[0];
        if (sel) {
          this.temporadaId.set(sel.id);
          this.temporadaNombre.set(sel.nombre || '');
          this.temporadaEstado.set(sel.estado || '');
        }
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  costoTotal = computed(() => {
    const c = parseFloat(this.form.cantidad) || 0;
    const p = parseFloat(this.form.precio_unitario) || 0;
    return Math.round(c * p * 100) / 100;
  });

  get puedeGuardar(): boolean {
    return !!this.form.categoria &&
           !!this.form.fecha_compra &&
           !!this.form.precio_unitario &&
           parseFloat(this.form.precio_unitario) > 0 &&
           !!this.temporadaId();
  }

  seleccionarCategoria(id: string) {
    this.form.categoria = id;
  }

  guardar() {
    if (!this.puedeGuardar) {
      this.error.set('Selecciona una categoría e indica fecha y precio unitario.');
      return;
    }

    this.guardando.set(true);
    this.error.set('');

    const cantidad = parseFloat(this.form.cantidad) || 1;
    const precio   = parseFloat(this.form.precio_unitario) || 0;

    const datos = {
      categoria:              this.form.categoria,
      producto_personalizado: this.form.producto_personalizado.trim() || null,
      cantidad,
      unidad_medida:          this.form.unidad_medida,
      precio_unitario:        precio,
      costo_total:            Math.round(cantidad * precio * 100) / 100,
      fecha_compra:           this.form.fecha_compra,
      proveedor:              this.form.proveedor.trim() || null,
    };

    this.svc.registrarCompra(this.temporadaId(), datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.router.navigate(['/app/finanzas'], {
          queryParams: { temporada: this.temporadaId() },
        });
      },
      error: (err) => {
        this.guardando.set(false);
        this.error.set(err.error?.error || 'No se pudo registrar el gasto.');
      },
    });
  }
}
