import { Component, OnInit, signal } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { AdminService } from '../services/admin.service';

@Component({
  selector: 'app-admin-fincas',
  standalone: true,
  imports: [CommonModule, DecimalPipe],
  template: `
    <div class="adm-page">
      <div class="adm-header">
        <h1>Fincas del sistema</h1>
        <p>{{ temporadas().length }} temporada(s) registradas en la plataforma</p>
      </div>

      @if (cargando()) {
        <div style="display:flex;flex-direction:column;gap:8px">
          @for (i of [1,2,3]; track i) {
            <div class="skeleton" style="height:90px;border-radius:8px"></div>
          }
        </div>
      }

      @if (!cargando()) {
        <div class="adm-tabla">
          <div class="adm-tabla__header">
            <span>Nombre</span>
            <span>Finca</span>
            <span>Cultivo</span>
            <span>Superficie</span>
            <span>Parcelas</span>
            <span>Inicio</span>
            <span>Estado</span>
          </div>
          @for (t of temporadas(); track t.id) {
            <div class="adm-tabla__row">
              <span class="nombre">{{ t.nombre }}</span>
              <span>{{ t.finca }}</span>
              <span>{{ t.cultivo }}</span>
              <span class="font-mono">
                {{ t.produccion?.superficie_total_ha | number:'1.2-2' }} ha
              </span>
              <span>{{ t.produccion?.total_parcelas }}</span>
              <span class="font-mono">{{ t.fechas?.inicio }}</span>
              <span>
                <span class="tag"
                      [class]="t.estado === 'activa' ? 'tag--verde' :
                               t.estado === 'cerrada' ? 'tag--gris' :
                               'tag--rojo'">
                  {{ t.estado }}
                </span>
              </span>
            </div>
          }
          @if (temporadas().length === 0) {
            <div class="adm-empty">
              <p>Sin temporadas registradas.</p>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    @use '../../../../styles' as *;
    .adm-page{display:flex;flex-direction:column;gap:$s4;animation:fadeIn .2s ease}
    .adm-header{padding-bottom:$s4;border-bottom:1px solid var(--border); h1{font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:3px} p{font-size:12px;color:var(--text-sec)}}
    .adm-tabla{background:var(--bg-surface);border:1px solid var(--border);border-radius:$radius-md;overflow:hidden;overflow-x:auto;
      &__header{display:grid;grid-template-columns:2fr 1.5fr 1fr 0.8fr 0.6fr 0.9fr 0.7fr;padding:$s2 $s4;background:var(--bg-app);border-bottom:1px solid var(--border);min-width:640px;
        span{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--text-ter)}}
      &__row{display:grid;grid-template-columns:2fr 1.5fr 1fr 0.8fr 0.6fr 0.9fr 0.7fr;padding:$s3 $s4;border-bottom:1px solid var(--border);align-items:center;min-width:640px;transition:$t-fast;
        &:last-child{border-bottom:none}&:hover{background:var(--bg-app)} span{font-size:12px;color:var(--text-sec)}}
    }
    .nombre{font-weight:600;color:var(--text-primary) !important}
    .adm-empty{padding:$s8;text-align:center; p{font-size:12px;color:var(--text-sec)}}
  `]
})
export class AdminFincasComponent implements OnInit {
  cargando   = signal(true);
  temporadas = signal<any[]>([]);

  constructor(private svc: AdminService) {}

  ngOnInit() {
    this.svc.listarTemporadas().subscribe({
      next: (r) => { this.temporadas.set(r.temporadas || []); this.cargando.set(false); },
      error: () => this.cargando.set(false),
    });
  }
}