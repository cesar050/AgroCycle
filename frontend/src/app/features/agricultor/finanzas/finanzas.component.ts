import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { FinanzasService } from './services/finanzas.service';

@Component({
  selector: 'app-finanzas',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe, RouterLink],
  templateUrl: './finanzas.component.html',
  styleUrl: './finanzas.component.scss'
})
export class FinanzasComponent implements OnInit {

  cargando      = signal(true);
  guardando     = signal(false);
  error         = signal('');
  errorForm     = signal('');
  tabActiva     = signal<'resumen'|'gastos'|'venta'>('resumen');
  mostrarForm   = signal(false);

  temporadas    = signal<any[]>([]);
  temporadaId   = signal('');
  gastos        = signal<any[]>([]);
  rentabilidad  = signal<any>(null);

  // Para venta de cosecha necesitamos temporada_parcela_id
  tpId          = signal('');
  parcelas      = signal<any[]>([]);

  // Formulario compra
  formCompra = {
    categoria:           '',
    producto_personalizado: '',
    cantidad:            '',
    unidad_medida:       'kg',
    precio_unitario:     '',
    fecha_compra:        '',
    proveedor:           '',
    insumo_id:           '',
  };

  // Formulario venta
  formVenta = {
    produccion_real_qq:  '',
    fecha_cosecha:       '',
    precio_venta_qq:     '',
    volumen_vendido_qq:  '',
    produccion_autoconsumo_qq: '',
  };

  categorias = [
    { id: 'semillas',      label: 'Semillas' },
    { id: 'fertilizantes', label: 'Fertilizantes' },
    { id: 'agroquimicos',  label: 'Agroquímicos' },
    { id: 'mano_obra',     label: 'Mano de obra' },
    { id: 'maquinaria',    label: 'Maquinaria' },
    { id: 'transporte',    label: 'Transporte' },
    { id: 'otros',         label: 'Otros' },
  ];

  unidades = ['kg', 'g', 'L', 'mL', 'unidad', 'saco', 'quintal', 'jornal'];

  constructor(private svc: FinanzasService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.svc.listarTemporadas().subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa');
        const seleccionada = activa || lista[0];
        if (seleccionada) {
          this.temporadaId.set(seleccionada.id);
          this.cargarDatos(seleccionada.id);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarDatos(temporadaId: string) {
    this.cargando.set(true);
    this.temporadaId.set(temporadaId);

    this.svc.listarGastos(temporadaId).subscribe({
      next: (res) => {
        this.gastos.set(res.compras || res.gastos || []);
      },
      error: () => {},
    });

    this.svc.calcularRentabilidad(temporadaId).subscribe({
      next: (res) => {
        this.rentabilidad.set(res);
        this.cargando.set(false);
        // Obtener tpId de las parcelas de la temporada
        if (res.parcelas?.length > 0) {
          this.tpId.set(res.parcelas[0].temporada_parcela_id || '');
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  abrirFormCompra() {
    this.formCompra = {
      categoria: '', producto_personalizado: '',
      cantidad: '', unidad_medida: 'kg',
      precio_unitario: '', fecha_compra: new Date().toISOString().split('T')[0],
      proveedor: '', insumo_id: '',
    };
    this.errorForm.set('');
    this.mostrarForm.set(true);
  }

  cerrarForm() {
    this.mostrarForm.set(false);
    this.errorForm.set('');
  }

  guardarCompra() {
    if (!this.formCompra.categoria || !this.formCompra.fecha_compra ||
        !this.formCompra.precio_unitario) {
      this.errorForm.set('Categoría, fecha y precio son requeridos.');
      return;
    }

    this.guardando.set(true);
    this.errorForm.set('');

    const cantidad = parseFloat(this.formCompra.cantidad) || 1;
    const precio   = parseFloat(this.formCompra.precio_unitario) || 0;

    const datos = {
      categoria:              this.formCompra.categoria,
      producto_personalizado: this.formCompra.producto_personalizado || null,
      cantidad,
      unidad_medida:    this.formCompra.unidad_medida,
      precio_unitario:  precio,
      costo_total:      Math.round(cantidad * precio * 100) / 100,
      fecha_compra:     this.formCompra.fecha_compra,
      proveedor:        this.formCompra.proveedor || null,
    };

    this.svc.registrarCompra(this.temporadaId(), datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.cerrarForm();
        this.cargarDatos(this.temporadaId());
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorForm.set(err.error?.error || 'Error al registrar el gasto.');
      }
    });
  }

  confirmarEliminarCompra(compra: any) {
    if (!confirm(`¿Eliminar el gasto de $${compra.costo_total}?`)) return;
    this.svc.eliminarCompra(compra.id).subscribe({
      next: () => this.cargarDatos(this.temporadaId()),
      error: () => {},
    });
  }

  guardarVenta() {
    if (!this.formVenta.produccion_real_qq || !this.formVenta.fecha_cosecha ||
        !this.formVenta.precio_venta_qq || !this.formVenta.volumen_vendido_qq) {
      this.error.set('Todos los campos de venta son requeridos.');
      return;
    }

    if (!this.tpId()) {
      this.error.set('No se encontró la parcela de la temporada.');
      return;
    }

    this.guardando.set(true);
    this.error.set('');

    const datos = {
      produccion_real_qq:       parseFloat(this.formVenta.produccion_real_qq),
      fecha_cosecha:            this.formVenta.fecha_cosecha,
      precio_venta_qq:          parseFloat(this.formVenta.precio_venta_qq),
      volumen_vendido_qq:       parseFloat(this.formVenta.volumen_vendido_qq),
      produccion_autoconsumo_qq: this.formVenta.produccion_autoconsumo_qq
        ? parseFloat(this.formVenta.produccion_autoconsumo_qq) : null,
    };

    this.svc.registrarVenta(this.tpId(), datos).subscribe({
      next: () => {
        this.guardando.set(false);
        this.formVenta = {
          produccion_real_qq: '', fecha_cosecha: '',
          precio_venta_qq: '', volumen_vendido_qq: '',
          produccion_autoconsumo_qq: '',
        };
        this.cargarDatos(this.temporadaId());
        this.tabActiva.set('resumen');
      },
      error: (err) => {
        this.guardando.set(false);
        this.error.set(err.error?.error || 'Error al registrar la venta.');
      }
    });
  }

  get costoCalculado(): number {
    const c = parseFloat(this.formCompra.cantidad) || 0;
    const p = parseFloat(this.formCompra.precio_unitario) || 0;
    return Math.round(c * p * 100) / 100;
  }

  get ingresosCalculados(): number {
    const vol   = parseFloat(this.formVenta.volumen_vendido_qq) || 0;
    const precio = parseFloat(this.formVenta.precio_venta_qq) || 0;
    return Math.round(vol * precio * 100) / 100;
  }

  labelCategoria(cat: string): string {
    return this.categorias.find(c => c.id === cat)?.label || cat;
  }

  colorCategoria(cat: string): string {
    const colores: Record<string, string> = {
      semillas: '#4CAF50', fertilizantes: '#2196F3',
      agroquimicos: '#F44336', mano_obra: '#FF9800',
      maquinaria: '#9C27B0', transporte: '#607D8B', otros: '#795548',
    };
    return colores[cat] || '#607D8B';
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }

  get gananciaPositiva(): boolean {
    return (this.rentabilidad()?.resultado?.ganancia_neta ?? 0) >= 0;
  }
}