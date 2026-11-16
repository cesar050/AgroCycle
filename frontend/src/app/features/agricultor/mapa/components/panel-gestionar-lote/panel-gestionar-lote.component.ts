import { Component, OnDestroy, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';
import { MapaService } from '../../services/mapa.service';
import { MapaStateService, Parcela } from '../../services/mapa-state.service';
import { calcularAreaHaAprox, puntoDentroDePoligono } from '../../mapa.utils';

// Panel embebido en el 20% de MapaComponent — reemplaza la antigua
// página routeada pages/nuevo-lote. Valida en el cliente que cada
// punto nuevo caiga dentro del límite real de la finca activa, igual
// que hacía la página original, pero dibujando sobre el mapa compartido.
@Component({
  selector: 'app-panel-gestionar-lote',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-gestionar-lote.component.html',
  styleUrl: './panel-gestionar-lote.component.scss',
})
export class PanelGestionarLoteComponent implements OnDestroy {
  state = inject(MapaStateService);
  private mapaService = inject(MapaService);

  modoCrear = computed(() => this.state.panelMode() === 'crear-lote');

  nombre = '';
  descripcion = '';

  cargando = signal(false);
  cargandoDatos = signal(false);
  error = signal('');
  errorEliminar = signal('');
  fueraDeLimite = signal(false);
  coordenadas = signal<[number, number][]>([]);
  areaHa = signal(0);

  loteActual = computed(() => {
    const id = this.state.loteEnContexto();
    return this.state.lotes().find(l => l.id === id) ?? null;
  });

  parcelasDelLote = computed<Parcela[]>(() => this.loteActual()?.parcelas ?? []);

  private puntosLatLng: L.LatLng[] = [];
  private marcadores: L.CircleMarker[] = [];
  private poligono: L.Polygon | null = null;
  private readonly onClick = (e: L.LeafletMouseEvent) => this.agregarPunto(e.latlng);

  constructor() {
    // Modo editar: precarga el formulario con el detalle real del lote
    // (nombre/descripción no vienen en el árbol de datosMapa, solo id/
    // nombre/superficie/geojson/parcelas).
    effect(() => {
      if (this.state.panelMode() !== 'editar-lote') return;
      const id = this.state.loteEnContexto();
      if (!id) return;
      this.cargandoDatos.set(true);
      this.mapaService.obtenerLote(id).subscribe({
        next: (res) => {
          this.nombre = res.nombre ?? '';
          this.descripcion = res.descripcion ?? '';
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

  private puntoDentroDeFinca(latlng: L.LatLng): boolean {
    const anillo = this.state.datosMapa()?.finca?.geojson?.coordinates?.[0];
    if (!anillo?.length) return true; // sin límite conocido: no bloquear
    return puntoDentroDePoligono(latlng.lat, latlng.lng, anillo);
  }

  private agregarPunto(latlng: L.LatLng): void {
    const mapa = this.state.mapaLeaflet();
    if (!mapa) return;

    if (!this.puntoDentroDeFinca(latlng)) {
      this.mostrarRechazo(latlng, mapa);
      return;
    }

    const marker = L.circleMarker(latlng, {
      radius: 5, fillColor: '#B45309', color: '#fff', weight: 2, fillOpacity: 1,
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
        color: '#B45309', weight: 2, fillColor: '#B45309', fillOpacity: 0.25,
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
        this.state.errorRefresco.set(null);
        this.state.volverAlVisor();
      },
      error: () => {
        this.state.errorRefresco.set(
          'El lote se guardó, pero no se pudo actualizar la vista del mapa. Recarga la página para ver los datos actualizados.'
        );
        this.state.volverAlVisor();
      },
    });
  }

  guardar(): void {
    if (!this.puedeGuardar) {
      this.error.set(
        this.modoCrear()
          ? 'Completa el nombre y dibuja al menos 3 puntos dentro de la finca.'
          : 'Completa el nombre del lote.'
      );
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    if (this.modoCrear()) {
      const finca = this.state.fincaActiva();
      if (!finca) return;
      const datos = {
        nombre: this.nombre.trim(),
        descripcion: this.descripcion.trim(),
        coordenadas: this.coordenadas(),
      };
      this.mapaService.registrarLote(finca.id, datos).subscribe({
        next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
        error: (err) => {
          this.cargando.set(false);
          this.error.set(err.error?.error || 'Error al guardar el lote.');
        },
      });
      return;
    }

    const loteId = this.state.loteEnContexto();
    if (!loteId) return;
    this.mapaService.editarLote(loteId, {
      nombre: this.nombre.trim(),
      descripcion: this.descripcion.trim(),
    }).subscribe({
      next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(err.error?.error || 'Error al editar el lote.');
      },
    });
  }

  eliminar(): void {
    const loteId = this.state.loteEnContexto();
    if (!loteId) return;
    this.errorEliminar.set('');
    this.cargando.set(true);

    this.mapaService.eliminarLote(loteId).subscribe({
      next: () => { this.cargando.set(false); this.refrescarMapaYVolver(); },
      error: (err) => {
        this.cargando.set(false);
        this.errorEliminar.set(err.error?.error || 'No se pudo eliminar el lote.');
      },
    });
  }

  seleccionarParcela(parcelaId: string): void {
    this.state.parcelaSeleccionadaId.set(parcelaId);
    this.state.panelMode.set('editar-parcela');
  }

  nuevaParcela(): void {
    this.state.panelMode.set('crear-parcela');
  }
}
