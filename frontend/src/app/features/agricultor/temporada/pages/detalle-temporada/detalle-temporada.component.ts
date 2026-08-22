import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { TemporadaService } from '../../services/temporada.service';

@Component({
  selector: 'app-detalle-temporada',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div style="padding:2rem">
      <a routerLink="/app/temporada">← Volver a temporadas</a>
      <h2 style="margin-top:1rem">Detalle de temporada</h2>
      <p style="color:#6C757D">En construcción para v1...</p>
    </div>
  `
})
export class DetalleTemporadaComponent implements OnInit {
  id = '';
  constructor(private route: ActivatedRoute) {}
  ngOnInit() {
    this.id = this.route.snapshot.paramMap.get('id') || '';
  }
}
