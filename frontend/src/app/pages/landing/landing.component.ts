import { Component, OnInit, OnDestroy, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss'
})
export class LandingComponent implements OnInit, OnDestroy {

  menuAbierto  = signal(false);
  scrolled     = signal(false);
  darkMode     = signal(false);
  anoActual    = new Date().getFullYear();

  problemas = [
    {
      icono: 'clima',
      titulo: 'Clima impredecible',
      descripcion: 'El bosque seco del sur del Ecuador tiene una sola temporada de lluvias al año. Un error de planificación significa doce meses de pérdida.',
    },
    {
      icono: 'datos',
      titulo: 'Decisiones sin datos',
      descripcion: 'El 94% de los agricultores familiares toman decisiones de siembra y riego basadas en experiencia empírica, sin acceso a datos técnicos.',
    },
    {
      icono: 'perdida',
      titulo: 'Pérdidas evitables',
      descripcion: 'El estrés hídrico en floración puede reducir el rendimiento hasta un 150% del déficit hídrico acumulado en la etapa crítica.',
    },
  ];

  soluciones = [
    {
      num: '01',
      titulo: 'Monitoreo climático continuo',
      desc: 'Datos históricos desde 1940 y pronóstico de 7 días vía Open-Meteo. Balance hídrico FAO-56 calculado diariamente sin sensores físicos.',
      tags: ['Open-Meteo API', 'FAO-56', 'Pronóstico 7 días'],
      color: 'azul',
    },
    {
      num: '02',
      titulo: 'Estimación de producción FAO-33',
      desc: 'Modelo de Stewart (1977) adaptado al bosque seco ecuatoriano. Calcula quintales por hectárea con desglose por etapa fenológica.',
      tags: ['Modelo FAO-33', 'Etapas fenológicas', 'Ks por etapa'],
      color: 'verde',
    },
    {
      num: '03',
      titulo: 'Control financiero de la temporada',
      desc: 'Gastos por categoría, ingresos por venta de cosecha y rentabilidad. Costo por quintal producido al cierre de cada temporada.',
      tags: ['Rentabilidad', 'Costo/quintal', 'Historial'],
      color: 'dorado',
    },
  ];

  metricas = [
    { valor: '71.24', unidad: 'qq/ha', desc: 'Producción estimada', sub: 'Parcela Choza · Bramaderos, Loja', color: 'verde' },
    { valor: '0.955', unidad: 'Ks',    desc: 'Estrés hídrico promedio', sub: 'Sin estrés en floración · FAO-56', color: 'azul' },
    { valor: '±8%',   unidad: 'error', desc: 'Precisión del modelo', sub: '151 días de datos reales validados', color: 'dorado' },
    { valor: '$484',  unidad: 'ganancia', desc: 'Rentabilidad real', sub: 'Temporada 2026-2027 · Finca Ramos', color: 'tierra' },
  ];

  audiencia = [
    {
      rol: 'Agricultor',
      icono: 'field',
      desc: 'Registra tu temporada, monitorea el clima de tu parcela y conoce cuánto vas a cosechar antes de que ocurra.',
      items: [
        'Dashboard con estado de la temporada',
        'Alertas de estrés hídrico',
        'Registro de actividades y gastos',
        'Ficha técnica PDF descargable',
      ],
      color: 'verde',
    },
    {
      rol: 'Agrónomo',
      icono: 'science',
      desc: 'Vincula tu perfil a fincas asignadas. Registra observaciones técnicas y recomendaciones con nivel de urgencia.',
      items: [
        'Observaciones técnicas por parcela',
        'Evaluaciones de campo con NDVI',
        'Recomendaciones con fecha límite',
        'Historial de intervenciones técnicas',
      ],
      color: 'azul',
    },
    {
      rol: 'Investigador',
      icono: 'data',
      desc: 'Accede a datos históricos validados del bosque seco ecuatoriano con historial climático y comparativos entre temporadas.',
      items: [
        'Historial climático con filtros',
        'Comparativo entre temporadas',
        'Modelo predictivo Ridge Regression',
        'Datos validados en campo real',
      ],
      color: 'dorado',
    },
  ];

  @HostListener('window:scroll')
  onScroll() {
    this.scrolled.set(window.scrollY > 60);
  }

  ngOnInit() {
    const saved = localStorage.getItem('agrocycle-dark');
    if (saved === 'true') { this.darkMode.set(true); document.body.classList.add('dark'); }
  }

  toggleMenu()    { this.menuAbierto.update(v => !v); }
  cerrarMenu()    { this.menuAbierto.set(false); }

  toggleDark() {
    this.darkMode.update(v => !v);
    document.body.classList.toggle('dark');
    localStorage.setItem('agrocycle-dark', String(this.darkMode()));
  }

  ngOnDestroy() {}
}