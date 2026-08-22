import {
  Component, OnInit, OnDestroy, signal,
  ViewChild, ElementRef, AfterViewInit
} from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ClimaticoService } from './services/climatico.service';

@Component({
  selector: 'app-climatico',
  standalone: true,
  imports: [CommonModule, FormsModule, DecimalPipe],
  templateUrl: './climatico.component.html',
  styleUrl: './climatico.component.scss'
})
export class ClimaticoComponent implements OnInit, AfterViewInit, OnDestroy {

  @ViewChild('graficaRef') graficaRef!: ElementRef;

  // Estado
  cargando        = signal(true);
  cargandoForecast = signal(false);
  guardandoManual  = signal(false);
  descargando      = signal(false);
  error            = signal('');
  tabActiva        = signal<'resumen'|'historial'|'forecast'|'manual'>('resumen');

  // Datos
  fincas    = signal<any[]>([]);
  parcelas  = signal<any[]>([]);
  temporadas = signal<any[]>([]);

  parcelaId      = signal('');
  parcelaNombre  = signal('');
  temporadaId    = signal('');
  tpId           = signal(''); // temporada_parcela_id

  resumenClima   = signal<any>(null);
  historial      = signal<any[]>([]);
  forecast       = signal<any[]>([]);
  alertas        = signal<any[]>([]);
  paginacion     = signal<any>(null);
  paginaActual   = signal(1);

  // Formulario evento manual
  formManual = {
    fecha:                      '',
    precipitacion_mm:           '',
    temperatura_max_c:          '',
    temperatura_min_c:          '',
    humedad_relativa_porcentaje: '',
    evapotranspiracion_mm:      '',
  };

  private grafica: any = null;

  constructor(private svc: ClimaticoService) {}

  ngOnInit() { this.cargarFincas(); }

  ngAfterViewInit() {}

  cargarFincas() {
    this.svc.listarFincas().subscribe({
      next: (res) => {
        const fincas = Array.isArray(res) ? res : (res.fincas || []);
        this.fincas.set(fincas);
        if (fincas.length > 0) {
          this.cargarParcelasDeTodasLasFincas(fincas);
        } else {
          this.cargando.set(false);
        }
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarParcelasDeTodasLasFincas(fincas: any[]) {
    this.buscarPrimeraParcelaDisponible(fincas, 0);
  }

  private buscarPrimeraParcelaDisponible(fincas: any[], indiceFinca: number) {
    if (indiceFinca >= fincas.length) {
      this.cargando.set(false);
      return;
    }

    this.svc.listarLotes(fincas[indiceFinca].id).subscribe({
      next: (res) => {
        const lotes = res.lotes || res || [];
        this.buscarParcelaEnLotes(fincas, indiceFinca, lotes, 0);
      },
      error: () => this.buscarPrimeraParcelaDisponible(fincas, indiceFinca + 1),
    });
  }

  private buscarParcelaEnLotes(
    fincas: any[], indiceFinca: number, lotes: any[], indiceLote: number
  ) {
    if (indiceLote >= lotes.length) {
      this.buscarPrimeraParcelaDisponible(fincas, indiceFinca + 1);
      return;
    }

    this.svc.listarParcelas(lotes[indiceLote].id).subscribe({
      next: (r) => {
        const p = r.parcelas || r || [];
        if (p.length > 0) {
          this.parcelas.set(p);
          this.seleccionarParcela(p[0].id, p[0].nombre);
        } else {
          this.buscarParcelaEnLotes(fincas, indiceFinca, lotes, indiceLote + 1);
        }
      },
      error: () => this.buscarParcelaEnLotes(fincas, indiceFinca, lotes, indiceLote + 1),
    });
  }

  seleccionarParcela(id: string, nombre: string) {
    this.parcelaId.set(id);
    this.parcelaNombre.set(nombre);
    this.cargarDatos();
  }

  cargarDatos() {
    this.cargando.set(true);

    // Cargar resumen climático
    this.svc.listarClima(this.parcelaId()).subscribe({
      next: (res) => {
        this.resumenClima.set(res);
        this.cargando.set(false);
        // Inicializar gráfica después del DOM
        setTimeout(() => this.inicializarGrafica(), 150);
      },
      error: () => this.cargando.set(false),
    });

    // Cargar historial
    this.cargarHistorial();

    // Cargar forecast
    this.cargarForecast();

    // Cargar alertas
    this.svc.generarAlertas().subscribe({
      next: (res) => this.alertas.set(res.alertas || []),
      error: () => this.alertas.set([]),
    });
  }

  cargarHistorial(pagina: number = 1) {
    this.svc.historialClimatico(this.parcelaId(), {
      pagina,
      por_pagina: 15,
    }).subscribe({
      next: (res) => {
        this.historial.set(res.datos || []);
        this.paginacion.set(res.paginacion || null);
        this.paginaActual.set(pagina);
      },
      error: () => {},
    });
  }

  cargarForecast() {
    this.cargandoForecast.set(true);
    this.svc.forecast(this.parcelaId()).subscribe({
      next: (res) => {
        this.forecast.set(res.forecast || res.pronostico || []);
        this.cargandoForecast.set(false);
      },
      error: () => this.cargandoForecast.set(false),
    });
  }

  descargarDatosHistoricos() {
    if (!this.parcelaId()) { return; }
    this.descargando.set(true);
    const hoy   = new Date();
    const inicio = new Date(hoy.getFullYear() - 1, hoy.getMonth(), hoy.getDate());

    this.svc.descargarClima(this.parcelaId(), {
      fecha_inicio: inicio.toISOString().split('T')[0],
      fecha_fin:    hoy.toISOString().split('T')[0],
    }).subscribe({
      next: () => {
        this.descargando.set(false);
        this.cargarHistorial();
        this.cargarDatos();
      },
      error: () => this.descargando.set(false),
    });
  }

  guardarEventoManual() {
    if (!this.formManual.fecha) {
      this.error.set('La fecha es requerida.');
      return;
    }

    this.guardandoManual.set(true);
    this.error.set('');

    const datos: any = { fecha: this.formManual.fecha };
    if (this.formManual.precipitacion_mm)
      datos.precipitacion_mm = parseFloat(this.formManual.precipitacion_mm);
    if (this.formManual.temperatura_max_c)
      datos.temperatura_max_c = parseFloat(this.formManual.temperatura_max_c);
    if (this.formManual.temperatura_min_c)
      datos.temperatura_min_c = parseFloat(this.formManual.temperatura_min_c);
    if (this.formManual.humedad_relativa_porcentaje)
      datos.humedad_relativa_porcentaje = parseFloat(
        this.formManual.humedad_relativa_porcentaje
      );
    if (this.formManual.evapotranspiracion_mm)
      datos.evapotranspiracion_mm = parseFloat(
        this.formManual.evapotranspiracion_mm
      );

    this.svc.registrarEventoManual(this.parcelaId(), datos).subscribe({
      next: () => {
        this.guardandoManual.set(false);
        this.formManual = {
          fecha: '', precipitacion_mm: '', temperatura_max_c: '',
          temperatura_min_c: '', humedad_relativa_porcentaje: '',
          evapotranspiracion_mm: '',
        };
        this.cargarHistorial();
        this.tabActiva.set('historial');
      },
      error: (err) => {
        this.guardandoManual.set(false);
        this.error.set(err.error?.error || 'Error al registrar el dato.');
      }
    });
  }

  private async inicializarGrafica() {
    if (!this.graficaRef?.nativeElement || this.grafica) return;
    const hist = this.historial();
    if (!hist.length) return;

    const { Chart, registerables } = await import('chart.js');
    Chart.register(...registerables);

    const ctx   = this.graficaRef.nativeElement.getContext('2d');
    const ultimos = hist.slice(0, 15).reverse();
    const fechas  = ultimos.map((d: any) => d.fecha?.slice(5)); // MM-DD
    const precip  = ultimos.map((d: any) => d.precipitacion_mm || 0);
    const tempMax = ultimos.map((d: any) => d.temperatura_max_c);
    const tempMin = ultimos.map((d: any) => d.temperatura_min_c);

    this.grafica = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: fechas,
        datasets: [
          {
            type: 'bar' as any,
            label: 'Lluvia (mm)',
            data: precip,
            backgroundColor: 'rgba(3,169,244,0.5)',
            borderColor: '#03A9F4',
            borderWidth: 1,
            yAxisID: 'y',
            borderRadius: 3,
            maxBarThickness: 20,
          },
          {
            type: 'line' as any,
            label: 'Temp. máx (°C)',
            data: tempMax,
            borderColor: '#F44336',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            pointRadius: 3,
            tension: 0.3,
            yAxisID: 'y1',
          },
          {
            type: 'line' as any,
            label: 'Temp. mín (°C)',
            data: tempMin,
            borderColor: '#2196F3',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            pointRadius: 3,
            tension: 0.3,
            yAxisID: 'y1',
          },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              font: { size: 11, family: 'Inter' },
              color: '#6C757D',
              boxWidth: 12,
              padding: 16,
            }
          },
          tooltip: {
            backgroundColor: '#212529',
            titleFont: { size: 11, family: 'Inter' },
            bodyFont:  { size: 11, family: 'JetBrains Mono' },
            padding: 10,
            cornerRadius: 6,
          }
        },
        scales: {
          x: {
            grid: { display: false },
            border: { display: false },
            ticks: { font: { size: 10 }, color: '#6C757D' }
          },
          y: {
            position: 'left',
            grid: { color: 'rgba(0,0,0,0.04)' },
            border: { display: false },
            title: {
              display: true,
              text: 'Lluvia (mm)',
              font: { size: 10 },
              color: '#03A9F4',
            },
            ticks: {
              font: { size: 10, family: 'JetBrains Mono' },
              color: '#6C757D',
            }
          },
          y1: {
            position: 'right',
            grid: { display: false },
            border: { display: false },
            title: {
              display: true,
              text: 'Temp. (°C)',
              font: { size: 10 },
              color: '#F44336',
            },
            ticks: {
              font: { size: 10, family: 'JetBrains Mono' },
              color: '#6C757D',
            }
          }
        }
      }
    });
  }

  iconoClima(desc: string): string {
    if (!desc) return 'cloud';
    const d = desc.toLowerCase();
    if (d.includes('lluvia') || d.includes('rain')) return 'rain';
    if (d.includes('sol') || d.includes('clear')) return 'sun';
    if (d.includes('nub') || d.includes('cloud')) return 'cloud';
    return 'cloud';
  }

  colorAlerta(tipo: string): string {
    if (tipo === 'alta') return 'tag--rojo';
    if (tipo === 'media') return 'tag--naranja';
    return 'tag--verde';
  }

  ngOnDestroy() {
    this.grafica?.destroy();
    this.grafica = null;
  }
}