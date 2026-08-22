import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AgronomoService } from '../services/agronomo.service';

@Component({
  selector: 'app-agronomo-fincas',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="page-base">
      <div class="page-header">
        <h1>Fincas asignadas</h1>
        <p>Fincas y cultivos bajo tu supervisión técnica</p>
      </div>
      @if (cargando()) {
        <div class="skeleton" style="height:200px;border-radius:8px"></div>
      }
      @if (!cargando()) {
        @for (t of temporadas(); track t.id) {
          <div class="finca-card">
            <div class="finca-card__header">
              <div>
                <h3>{{ t.finca }}</h3>
                <p>{{ t.nombre }} · {{ t.cultivo }}</p>
              </div>
              <span class="tag" [class]="t.estado === 'activa' ? 'tag--verde' : 'tag--gris'">
                {{ t.estado }}
              </span>
            </div>
            <div class="finca-card__datos">
              <div class="kv"><span>Inicio</span><span class="font-mono">{{ t.fechas?.inicio }}</span></div>
              <div class="kv"><span>Superficie</span><span class="font-mono">{{ t.produccion?.superficie_total_ha }} ha</span></div>
              <div class="kv"><span>Parcelas</span><span>{{ t.produccion?.total_parcelas }}</span></div>
            </div>
          </div>
        }
        @if (temporadas().length === 0) {
          <div class="empty-base">
            <p>No hay fincas asignadas.</p>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    @use '../../../../styles' as *;
    .page-base { display:flex;flex-direction:column;gap:$s4;animation:fadeIn .2s ease; }
    .page-header { padding-bottom:$s4;border-bottom:1px solid var(--border); h1{font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:3px} p{font-size:12px;color:var(--text-sec)} }
    .finca-card { background:var(--bg-surface);border:1px solid var(--border);border-radius:$radius-md;overflow:hidden;
      &__header{display:flex;align-items:flex-start;justify-content:space-between;padding:$s4;border-bottom:1px solid var(--border);gap:$s3; h3{font-size:14px;font-weight:700;color:var(--text-primary);margin-bottom:2px} p{font-size:12px;color:var(--text-sec)}}
      &__datos{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--border)}
    }
    .kv{background:var(--bg-surface);padding:$s3 $s4;display:flex;flex-direction:column;gap:2px; span:first-child{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--text-ter)} span:last-child{font-size:12px;font-weight:600;color:var(--text-primary)}}
    .empty-base{display:flex;align-items:center;justify-content:center;min-height:30vh; p{font-size:13px;color:var(--text-sec)}}
  `]
})
export class AgronomoFincasComponent implements OnInit {
  cargando   = signal(true);
  temporadas = signal<any[]>([]);
  constructor(private svc: AgronomoService) {}
  ngOnInit() {
    this.svc.listarTemporadas().subscribe({
      next: (r) => { this.temporadas.set(r.temporadas || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }
}
