import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hero.component.html',
  styleUrl: './hero.component.scss'
})
export class HeroComponent implements OnInit {
  // Contador animado para el número principal
  valorAnimado = signal(0);
  readonly valorFinal = 71.24;

  // Datos del dashboard demo flotante
  metricas = [
    {
      etiqueta: 'Producción estimada',
      valor: '71.24',
      unidad: 'qq/ha',
      icono: '🌽',
      color: 'verde',
      tendencia: '+8% vs temporada anterior'
    },
    {
      etiqueta: 'Humedad del suelo',
      valor: '95.5',
      unidad: '% Ks',
      icono: '💧',
      color: 'azul',
      tendencia: 'Condiciones óptimas'
    },
    {
      etiqueta: 'Días desde siembra',
      valor: '227',
      unidad: 'DDS',
      icono: '📅',
      color: 'dorado',
      tendencia: 'Etapa: Cosecha'
    },
    {
      etiqueta: 'Superficie monitoreada',
      valor: '0.67',
      unidad: 'ha',
      icono: '🗺️',
      color: 'tierra',
      tendencia: 'Parcela Choza activa'
    }
  ];

  ngOnInit() {
    this.animarContador();
  }

  private animarContador() {
    const duracion = 2000;
    const pasos = 60;
    const incremento = this.valorFinal / pasos;
    let actual = 0;
    let paso = 0;

    const intervalo = setInterval(() => {
      paso++;
      actual = Math.min(actual + incremento, this.valorFinal);
      this.valorAnimado.set(Math.round(actual * 100) / 100);

      if (paso >= pasos) {
        clearInterval(intervalo);
        this.valorAnimado.set(this.valorFinal);
      }
    }, duracion / pasos);
  }
}