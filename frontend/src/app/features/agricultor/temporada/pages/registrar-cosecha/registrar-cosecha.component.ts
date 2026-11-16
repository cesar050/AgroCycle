import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TemporadaService } from '../../services/temporada.service';
import { NotificacionService } from '../../../../../core/services/notificacion.service';

@Component({
  selector: 'app-registrar-cosecha',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, DecimalPipe],
  templateUrl: './registrar-cosecha.component.html',
  styleUrl: './registrar-cosecha.component.scss'
})
export class RegistrarCosechaComponent implements OnInit {

  temporadaId = '';
  tpId        = '';

  // Formulario — 5 campos reales + observaciones
  produccionRealQq        = '';
  fechaCosecha            = '';
  precioVentaQq           = '';
  volumenVendidoQq        = '';
  produccionAutoconsumoQq = '';
  observaciones           = '';

  cargando  = signal(false);
  error     = signal('');
  nombreTemporada = signal('');
  parcelaRef      = signal('');

  // Ingreso estimado (precio x volumen vendido)
  ingresoEstimado(): number | null {
    const precio = parseFloat(this.precioVentaQq);
    const vol    = parseFloat(this.volumenVendidoQq);
    if (!isNaN(precio) && !isNaN(vol)) return precio * vol;
    return null;
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private svc: TemporadaService,
    private notificacion: NotificacionService,
  ) {}

  ngOnInit() {
    this.temporadaId = this.route.snapshot.paramMap.get('id') || '';
    this.tpId        = this.route.snapshot.paramMap.get('tpId') || '';
    this.fechaCosecha = new Date().toISOString().split('T')[0];
    this.cargarContexto();
  }

  cargarContexto() {
    this.svc.obtener(this.temporadaId).subscribe({
      next: (res) => {
        this.nombreTemporada.set(res.nombre || '');
        const p = (res.parcelas || []).find((x: any) => x.id === this.tpId);
        if (p?.parcela_id) {
          this.parcelaRef.set('#' + String(p.parcela_id).slice(0, 8).toUpperCase());
        }
      },
      error: () => {}
    });
  }

  get puedeGuardar(): boolean {
    return !!this.produccionRealQq &&
           parseFloat(this.produccionRealQq) > 0 &&
           !!this.fechaCosecha;
  }

  guardar() {
    if (!this.puedeGuardar) {
      this.error.set('La producción real (qq) y la fecha de cosecha son obligatorias.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    const datos: any = {
      produccion_real_qq: parseFloat(this.produccionRealQq),
      fecha_cosecha:      this.fechaCosecha,
      precio_venta_qq:          this.precioVentaQq ? parseFloat(this.precioVentaQq) : null,
      volumen_vendido_qq:       this.volumenVendidoQq ? parseFloat(this.volumenVendidoQq) : null,
      produccion_autoconsumo_qq: this.produccionAutoconsumoQq ? parseFloat(this.produccionAutoconsumoQq) : null,
      observaciones: this.observaciones.trim() || null,
    };

    this.svc.registrarCosecha(this.temporadaId, this.tpId, datos).subscribe({
      next: () => {
        this.cargando.set(false);
        this.notificacion.exito('Cosecha registrada correctamente.');
        this.router.navigate(['/app/temporada', this.temporadaId]);
      },
      error: (err) => {
        this.cargando.set(false);
        const mensaje = err.error?.error || 'No se pudo registrar la cosecha.';
        this.error.set(mensaje);
        this.notificacion.error(mensaje);
      }
    });
  }
}
