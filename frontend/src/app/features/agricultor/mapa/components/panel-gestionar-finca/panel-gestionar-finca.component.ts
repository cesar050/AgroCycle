import { Component, OnDestroy, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import * as L from 'leaflet';
import { MapaService } from '../../services/mapa.service';
import { MapaStateService } from '../../services/mapa-state.service';
import { FincaContextService } from '../../../../../core/services/finca-context.service';
import { NotificacionService } from '../../../../../core/services/notificacion.service';
import { calcularAreaHaAprox } from '../../mapa.utils';

// Panel embebido en el 20% de MapaComponent — reemplaza las antiguas
// páginas routeadas pages/nueva-finca. Dibuja el polígono directamente
// sobre el mapa compartido (state.mapaLeaflet()) en vez de crear uno
// propio, y nunca navega: refresca los Signals del mapa al guardar.
@Component({
  selector: 'app-panel-gestionar-finca',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-gestionar-finca.component.html',
  styleUrl: './panel-gestionar-finca.component.scss',
})
export class PanelGestionarFincaComponent implements OnDestroy {
  state = inject(MapaStateService);
  private mapaService = inject(MapaService);
  private fincaContext = inject(FincaContextService);
  private notificacion = inject(NotificacionService);

  modoCrear = computed(() => this.state.panelMode() === 'crear-finca');

  nombre = '';
  provincia = '';
  canton = '';
  parroquia = '';
  sector = '';
  descripcion = '';

  cargando = signal(false);
  error = signal('');
  errorEliminar = signal('');
  coordenadas = signal<[number, number][]>([]);
  areaHa = signal(0);

  private puntosLatLng: L.LatLng[] = [];
  private marcadores: L.CircleMarker[] = [];
  private poligono: L.Polygon | null = null;
  private readonly onClick = (e: L.LeafletMouseEvent) => this.agregarPunto(e.latlng);

  constructor() {
    // Modo editar: precarga el formulario con la finca activa.
    effect(() => {
      if (this.state.panelMode() !== 'editar-finca') return;
      const f = this.state.fincaActiva();
      if (!f) return;
      this.nombre = f.nombre ?? '';
      this.provincia = f.provincia ?? '';
      this.canton = f.canton ?? '';
      this.parroquia = f.parroquia ?? '';
      this.sector = f.sector ?? '';
      this.descripcion = f.descripcion ?? '';
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

  private agregarPunto(latlng: L.LatLng): void {
    const mapa = this.state.mapaLeaflet();
    if (!mapa) return;
    const marker = L.circleMarker(latlng, {
      radius: 6, fillColor: '#15803D', color: '#fff', weight: 2, fillOpacity: 1,
    }).addTo(mapa);
    this.puntosLatLng.push(latlng);
    this.marcadores.push(marker);
    this.redibujarPoligono();
  }

  private redibujarPoligono(): void {
    const mapa = this.state.mapaLeaflet();
    if (!mapa) return;
    if (this.poligono) { mapa.removeLayer(this.poligono); this.poligono = null; }
    if (this.puntosLatLng.length >= 3) {
      this.poligono = L.polygon(this.puntosLatLng, {
        color: '#15803D', weight: 2, fillColor: '#15803D', fillOpacity: 0.2,
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

  guardar(): void {
    if (!this.puedeGuardar) {
      this.error.set(
        this.modoCrear()
          ? 'Completa el nombre y dibuja al menos 3 puntos en el mapa.'
          : 'Completa el nombre de la finca.'
      );
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    const datos: any = {
      nombre: this.nombre.trim(),
      provincia: this.provincia.trim(),
      canton: this.canton.trim(),
      parroquia: this.parroquia.trim(),
      sector: this.sector.trim(),
      descripcion: this.descripcion.trim(),
    };

    if (this.modoCrear()) {
      datos.coordenadas = this.coordenadas();
      this.mapaService.registrarFinca(datos).subscribe({
        next: (res) => {
          this.cargando.set(false);
          this.fincaContext.agregarFincaYSeleccionar(res);
          this.notificacion.exito(`Finca "${res.nombre}" registrada correctamente.`);
          this.state.volverAlVisor();
        },
        error: (err) => {
          this.cargando.set(false);
          const mensaje = err.error?.error || 'Error al guardar la finca. Intenta de nuevo.';
          this.error.set(mensaje);
          this.notificacion.error(mensaje);
        },
      });
      return;
    }

    const finca = this.state.fincaActiva();
    if (!finca) return;

    this.mapaService.editarFinca(finca.id, datos).subscribe({
      next: () => {
        this.cargando.set(false);
        // El caso de uso de edición no devuelve todos los campos editables;
        // se refleja localmente lo que sí se envió y se confirmó con éxito.
        this.fincaContext.actualizarFincaEnLista({ ...finca, ...datos });
        this.notificacion.exito(`Finca "${datos.nombre}" actualizada correctamente.`);
        this.state.volverAlVisor();
      },
      error: (err) => {
        this.cargando.set(false);
        const mensaje = err.error?.error || 'Error al editar la finca.';
        this.error.set(mensaje);
        this.notificacion.error(mensaje);
      },
    });
  }

  eliminar(): void {
    const finca = this.state.fincaActiva();
    if (!finca) return;
    this.errorEliminar.set('');
    this.cargando.set(true);

    this.mapaService.eliminarFinca(finca.id).subscribe({
      next: () => {
        this.cargando.set(false);
        this.fincaContext.eliminarFincaDeLista(finca.id);
        this.notificacion.exito(`Finca "${finca.nombre}" eliminada correctamente.`);
        this.state.volverAlVisor();
      },
      error: (err) => {
        this.cargando.set(false);
        const mensaje = err.error?.error || 'No se pudo eliminar la finca.';
        this.errorEliminar.set(mensaje);
        this.notificacion.error(mensaje);
      },
    });
  }

  seleccionarLote(loteId: string): void {
    this.state.loteEnContexto.set(loteId);
    this.state.panelMode.set('editar-lote');
  }

  nuevoLote(): void {
    this.state.panelMode.set('crear-lote');
  }
}
