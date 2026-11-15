import { Component, OnDestroy, OnInit, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';
import { MapaService } from '../../services/mapa.service';
import { MapaStateService } from '../../services/mapa-state.service';
import { calcularAreaHaAprox, puntoDentroDePoligono } from '../../mapa.utils';

// Panel embebido en el 20% de MapaComponent — reemplaza la antigua
// página routeada pages/nueva-parcela (cuyo template estaba vacío y
// no renderizaba nada). Valida en el cliente que cada punto nuevo
// caiga dentro del límite real del lote padre.
@Component({
  selector: 'app-panel-gestionar-parcela',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-gestionar-parcela.component.html',
  styleUrl: './panel-gestionar-parcela.component.scss',
})
export class PanelGestionarParcelaComponent implements OnInit, OnDestroy {
  state = inject(MapaStateService);
  private mapaService = inject(MapaService);

  modoCrear = computed(() => this.state.panelMode() === 'crear-parcela');

  nombre = '';
  tipoSueloId: number | null = null;
  drenaje = 'moderado';
  accesoRiego = false;
  tipoRiego = '';
  observaciones = '';

  drenajeOpciones = ['bueno', 'moderado', 'deficiente'];
  tiposRiego = ['Goteo', 'Aspersión', 'Gravedad', 'Manual'];
  tiposSuelo = signal<{ id: number; nombre: string }[]>([]);

  cargando = signal(false);
  cargandoDatos = signal(false);
  error = signal('');
  errorEliminar = signal('');
  fueraDeLimite = signal(false);
  coordenadas = signal<[number, number][]>([]);
  areaHa = signal(0);

  private puntosLatLng: L.LatLng[] = [];
  private marcadores: L.CircleMarker[] = [];
  private poligono: L.Polygon | null = null;
  private readonly onClick = (e: L.LeafletMouseEvent) => this.agregarPunto(e.latlng);

  constructor() {
    // Modo editar: precarga el formulario con el detalle real de la parcela.
    effect(() => {
      if (this.state.panelMode() !== 'editar-parcela') return;
      const id = this.state.parcelaSeleccionadaId();
      if (!id) return;
      this.cargandoDatos.set(true);
      this.mapaService.obtenerParcela(id).subscribe({
        next: (res) => {
          this.nombre = res.nombre ?? '';
          this.tipoSueloId = res.tipo_suelo_id ?? null;
          this.drenaje = res.drenaje ?? 'moderado';
          this.accesoRiego = !!res.acceso_riego;
          this.tipoRiego = res.tipo_riego ?? '';
          this.observaciones = res.observaciones ?? '';
          this.cargandoDatos.set(false);
        },
        error: () => this.cargandoDatos.set(false),
      });
    });

    // Modo crear: habilita dibujo por clic sobre el mapa compartido.
    effect((onCleanup) => {
      const mapa = this.state.mapaLeaflet();
      if (!mapa || !this.modoCrear()) return;
      mapa.on('click', this.onClick);
      onCleanup(() => mapa.off('click', this.onClick));
    });
  }

  ngOnInit(): void {
    this.mapaService.listarTiposSuelo().subscribe({
      next: (res) => this.tiposSuelo.set(res.tipos_suelo ?? []),
      error: () => this.tiposSuelo.set([]),
    });
  }

  ngOnDestroy(): void {
    this.limpiarDibujo();
  }

  get puntosDefinidos(): number {
    return this.puntosLatLng.length;
  }

  get puedeGuardar(): boolean {
    if (!this.nombre.trim()) return false;
    return this.modoCrear() ? this.coordenadas().length >= 3 : true;
  }

  private puntoDentroDelLote(latlng: L.LatLng): boolean {
    const loteId = this.state.loteEnContexto();
    const anillo = this.state.lotes().find(l => l.id === loteId)?.geojson?.coordinates?.[0];
    if (!anillo?.length) return true; // sin límite conocido: no bloquear
    return puntoDentroDePoligono(latlng.lat, latlng.lng, anillo);
  }

  private agregarPunto(latlng: L.LatLng): void {
    const mapa = this.state.mapaLeaflet();
    if (!mapa) return;

    if (!this.puntoDentroDelLote(latlng)) {
      this.mostrarRechazo(latlng, mapa);
      return;
    }

    const marker = L.circleMarker(latlng, {
      radius: 5, fillColor: '#15803D', color: '#fff', weight: 2, fillOpacity: 1,
    }).addTo(mapa);
    this.puntosLatLng.push(latlng);
    this.marcadores.push(marker);
    this.redibujarPoligono();
  }

  private mostrarRechazo(latlng: L.LatLng, mapa: L.Map): void {
    const marcador = L.circleMarker(latlng, {
      radius: 10, fillColor: '#DC2626', color: '#DC2626', weight: 2, fillOpacity: 0.35,
    }).addTo(mapa);
    this.fueraDeLimite.set(true);
    setTimeout(() => {
      mapa.removeLayer(marcador);
      this.fueraDeLimite.set(false);
    }, 1800);
  }

  private redibujarPoligono(): void {
    const mapa = this.state.mapaLeaflet();
    if (!mapa) return;
    if (this.poligono) { mapa.removeLayer(this.poligono); this.poligono = null; }
    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#15803D', weight: 2, fillColor: '#15803D', fillOpacity: 0.3,
      }).addTo(mapa);
      this.areaHa.set(calcularAreaHaAprox(this.puntosLatLng.map(p => ({ lat: p.lat, lng: p.lng }))));
    } else {
      this.areaHa.set(0);
    }
    this.coordenadas.set(this.puntosLatLng.map(p => [p.lng, p.lat]));
  }

  deshacerUltimoPunto(): void {
    if (!this.puntosLatLng.length) return;
    const mapa = this.state.mapaLeaflet();
    const marker = this.marcadores.pop();
    if (marker && mapa) mapa.removeLayer(marker);
    this.puntosLatLng.pop();
    this.redibujarPoligono();
  }

  limpiarDibujo(): void {
    try {
      const mapa = this.state.mapaLeaflet();
      if (mapa) {
        this.marcadores.forEach(m => mapa.removeLayer(m));
        if (this.poligono) mapa.removeLayer(this.poligono);
      }
    } catch {
      // El mapa ya pudo haber sido destruido (ej. al guardar con éxito).
    }
    this.marcadores = [];
    this.puntosLatLng = [];
    this.poligono = null;
    this.coordenadas.set([]);
    this.areaHa.set(0);
  }

  private refrescarMapaYVolver(): void {
    const finca = this.state.fincaActiva();
    if (!finca) { this.state.volverAlVisor(); return; }
    this.mapaService.obtenerMapaFinca(finca.id).subscribe({
      next: (res) => {
        this.state.datosMapa.set(res);
        this.state.volverAlVisor();
      },
      error: () => this.state.volverAlVisor(),
    });
  }

  guardar(): void {
    if (!this.puedeGuardar) {
      this.error.set(
        this.modoCrear()
          ? 'Completa el nombre y dibuja al menos 3 puntos dentro del lote.'
          : 'Completa el nombre de la parcela.'
      );
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    if (this.modoCrear()) {
      const loteId = this.state.loteEnContexto();
      if (!loteId) return;
      const datos = {
        nombre: this.nombre.trim(),
        coordenadas: this.coordenadas(),
        tipo_suelo_id: this.tipoSueloId,
        drenaje: this.drenaje,
        acceso_riego: this.accesoRiego,
        tipo_riego: this.accesoRiego ? this.tipoRiego : null,
        observaciones: this.observaciones.trim(),
      };
      this.mapaService.registrarParcela(loteId, datos).subscribe({
        next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.error?.error || 'Error al guardar la parcela.');
        },
      });
      return;
    }

    const parcelaId = this.state.parcelaSeleccionadaId();
    if (!parcelaId) return;
    this.mapaService.editarParcela(parcelaId, {
      nombre: this.nombre.trim(),
      tipo_suelo_id: this.tipoSueloId,
      drenaje: this.drenaje,
      acceso_riego: this.accesoRiego,
      tipo_riego: this.accesoRiego ? this.tipoRiego : null,
      observaciones: this.observaciones.trim(),
    }).subscribe({
      next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'Error al editar la parcela.');
      },
    });
  }

  eliminar(): void {
    const parcelaId = this.state.parcelaSeleccionadaId();
    if (!parcelaId) return;
    this.errorEliminar.set('');
    this.cargando.set(true);

    this.mapaService.eliminarParcela(parcelaId).subscribe({
      next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
      error: (err) => {
        this.cargando.set(false);
        this.errorEliminar.set(err.error?.error || 'No se pudo eliminar la parcela.');
      },
    });
  }
}
