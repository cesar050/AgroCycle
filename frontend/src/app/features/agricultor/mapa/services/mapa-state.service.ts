import { Injectable, inject, signal, computed } from '@angular/core';
import type { Map as LeafletMap } from 'leaflet';
import { FincaContextService } from '../../../../core/services/finca-context.service';
import {
  calcularEstadoParcela, generarRecomendaciones,
  EstadoParcela, Recomendacion,
  Parcela, Lote, Finca, TopografiaParcela, HumedadParcela,
} from '../mapa.utils';

export type { Parcela, Lote, Finca, TopografiaParcela, HumedadParcela };

export type CapaKey = 'parcelas' | 'estado' | 'agua' | 'pendiente' | 'altitud' | 'ndvi';
export type MapaBase = 'satelite' | 'relieve' | 'claro';
export type OrdenParcelas = 'nombre' | 'superficie' | 'estado';

// Estado del panel técnico del 20%: 'visor' es la vista normal de
// KPIs/tabla; el resto son los formularios transaccionales de
// Gestionar Fincas/Lotes/Parcelas embebidos dentro de MapaComponent.
export type PanelMode =
  | 'visor'
  | 'crear-finca' | 'editar-finca'
  | 'crear-lote' | 'editar-lote'
  | 'crear-parcela' | 'editar-parcela';

// Provisto a nivel de MapaComponent (no root): cada vez que se entra a la
// ruta /app/mapa se crea una instancia nueva, así ningún estado de una
// finca anterior se queda pegado en la siguiente visita.
@Injectable()
export class MapaStateService {
  // Expuesto (no privado): el selector de finca flotante del mapa necesita
  // leer la lista completa de fincas y poder cambiar la activa desde el
  // template. No se añade ningún dato ni método nuevo — mismo servicio que
  // ya se usaba internamente, solo visible ahora fuera de esta clase.
  fincaContext = inject(FincaContextService);

  // La finca activa vive en FincaContextService (compartida con el
  // selector del sidebar del layout) — el mapa solo la refleja, nunca
  // mantiene su propia copia, así cambiar de finca desde el sidebar
  // actualiza el mapa automáticamente.
  fincaActiva = computed(() => this.fincaContext.fincaActiva());

  // Carga de la LISTA de fincas (sidebar). Distinta de `cargando`, que es
  // la carga de los datos del mapa de la finca ya seleccionada.
  cargandoFincas = computed(() => this.fincaContext.cargando());

  // ---------------- Datos remotos ----------------
  cargando       = signal(true);
  datosMapa      = signal<{ finca: Finca } | null>(null);
  datosTopografia = signal<{ parcelas: TopografiaParcela[] } | null>(null);
  datosHumedad    = signal<{ parcelas: HumedadParcela[] } | null>(null);
  ndviUrl         = signal<string | null>(null);

  // ---------------- Filtros panel izquierdo ----------------
  busqueda    = signal('');
  filtroEtapa = signal<string>('todas');
  ordenPor    = signal<OrdenParcelas>('nombre');

  // ---------------- UI de paneles ----------------
  panelIzquierdoColapsado = signal(false);
  drawerHistorialAbierto  = signal(false);
  seccionesExpandidas = signal<Record<string, boolean>>({
    estado: true, agua: true, produccion: true, terreno: true, recomendaciones: true,
  });

  // ---------------- Capas y mapa base ----------------
  capasActivas = signal<Set<CapaKey>>(new Set<CapaKey>(['parcelas', 'estado']));
  mapaBase     = signal<MapaBase>('satelite');
  cursorLatLng = signal<{ lat: number; lng: number } | null>(null);

  // ---------------- Selección ----------------
  parcelaSeleccionadaId = signal<string | null>(null);

  // ---------------- Panel de gestión (CRUD inline) ----------------
  // Instancia única de Leaflet compartida por MapaComponent y los tres
  // paneles de gestión: así "Gestionar Finca/Lote/Parcela" dibuja sobre
  // el mismo mapa del 80% en vez de crear uno nuevo.
  mapaLeaflet = signal<LeafletMap | null>(null);
  panelMode = signal<PanelMode>('visor');
  // Lote sobre el que opera el panel actual (editar-lote, o el lote
  // padre al crear/editar una parcela). null en los demás modos.
  loteEnContexto = signal<string | null>(null);

  // ================================================================
  // Computeds
  // ================================================================
  lotes = computed<Lote[]>(() => this.datosMapa()?.finca?.lotes ?? []);

  parcelas = computed<Parcela[]>(() => this.lotes().flatMap(l => l.parcelas ?? []));

  totalParcelas = computed(() => this.parcelas().length);

  areaCultivada = computed(() =>
    this.parcelas().reduce((s, p) => s + (p.superficie_ha || 0), 0)
  );

  humedadPorParcela = computed(() => {
    const mapa = new Map<string, HumedadParcela>();
    (this.datosHumedad()?.parcelas ?? []).forEach(h => mapa.set(h.parcela_id, h));
    return mapa;
  });

  topografiaPorParcela = computed(() => {
    const mapa = new Map<string, TopografiaParcela>();
    (this.datosTopografia()?.parcelas ?? []).forEach(t => mapa.set(t.parcela_id, t));
    return mapa;
  });

  estadosPorParcela = computed(() => {
    const humedad = this.humedadPorParcela();
    const mapa = new Map<string, EstadoParcela>();
    this.parcelas().forEach(p => mapa.set(p.id, calcularEstadoParcela(p, humedad.get(p.id))));
    return mapa;
  });

  parcelasConAtencion = computed(() => {
    const estados = this.estadosPorParcela();
    return this.parcelas().filter(p => {
      const tono = estados.get(p.id)?.tono;
      return tono === 'rojo' || tono === 'amarillo';
    }).length;
  });

  parcelasFiltradas = computed<Parcela[]>(() => {
    let lista = this.parcelas();

    const q = this.busqueda().trim().toLowerCase();
    if (q) lista = lista.filter(p => p.nombre.toLowerCase().includes(q));

    const etapa = this.filtroEtapa();
    if (etapa !== 'todas') {
      lista = lista.filter(p => (p.estado_fenologico ?? 'sin_etapa') === etapa);
    }

    const orden = this.ordenPor();
    lista = [...lista];
    if (orden === 'nombre') {
      lista.sort((a, b) => a.nombre.localeCompare(b.nombre));
    } else if (orden === 'superficie') {
      lista.sort((a, b) => (b.superficie_ha || 0) - (a.superficie_ha || 0));
    } else if (orden === 'estado') {
      const estados = this.estadosPorParcela();
      const rango: Record<string, number> = { rojo: 0, amarillo: 1, verde: 2, gris: 3 };
      lista.sort((a, b) =>
        (rango[estados.get(a.id)?.tono ?? 'gris'] ?? 9) -
        (rango[estados.get(b.id)?.tono ?? 'gris'] ?? 9)
      );
    }
    return lista;
  });

  parcelaSeleccionada = computed<Parcela | null>(() => {
    const id = this.parcelaSeleccionadaId();
    if (!id) return null;
    return this.parcelas().find(p => p.id === id) ?? null;
  });

  recomendacionesSeleccionada = computed<Recomendacion[]>(() => {
    const p = this.parcelaSeleccionada();
    if (!p) return [];
    return generarRecomendaciones(
      p,
      this.humedadPorParcela().get(p.id),
      this.topografiaPorParcela().get(p.id),
    );
  });

  // ================================================================
  // Mutadores
  // ================================================================
  seleccionarParcela(id: string | null): void {
    this.parcelaSeleccionadaId.set(id);
  }

  cerrarPanelDerecho(): void {
    this.parcelaSeleccionadaId.set(null);
  }

  toggleCapa(key: CapaKey): void {
    this.capasActivas.update(set => {
      const nuevo = new Set(set);
      if (nuevo.has(key)) nuevo.delete(key); else nuevo.add(key);
      return nuevo;
    });
  }

  toggleSeccion(nombre: string): void {
    this.seccionesExpandidas.update(s => ({ ...s, [nombre]: !s[nombre] }));
  }

  // Restaura el panel técnico a la vista normal — usado por el botón
  // "[← Regresar al Mapa General]" y tras guardar/eliminar con éxito.
  volverAlVisor(): void {
    this.panelMode.set('visor');
    this.loteEnContexto.set(null);
  }

  // Se llama cuando fincaActiva() cambia: limpia todo lo que dependía
  // de la finca anterior (selección, capas cargadas bajo demanda, filtros).
  resetSeleccionFinca(): void {
    this.parcelaSeleccionadaId.set(null);
    this.datosTopografia.set(null);
    this.datosHumedad.set(null);
    this.busqueda.set('');
    this.filtroEtapa.set('todas');
    this.volverAlVisor();
    const urlAnterior = this.ndviUrl();
    if (urlAnterior) URL.revokeObjectURL(urlAnterior);
    this.ndviUrl.set(null);
  }
}
