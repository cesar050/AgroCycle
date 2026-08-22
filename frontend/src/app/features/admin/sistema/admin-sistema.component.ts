import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-admin-sistema',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="sys-page">
      <div class="sys-header">
        <h1>Monitor del sistema</h1>
        <p>Estado de servicios, APIs y configuración</p>
      </div>

      <div class="sys-grid">

        <!-- Backend -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>Backend Flask</h3>
            <span class="sys-status ok">
              <span class="sys-dot"></span>
              Online
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>Versión</span><span class="font-mono">Flask 3.x · Python 3.11</span></div>
            <div class="sys-kv"><span>Arquitectura</span><span>Clean Architecture</span></div>
            <div class="sys-kv"><span>Puerto</span><span class="font-mono">5000</span></div>
            <div class="sys-kv"><span>CORS</span><span>Habilitado</span></div>
          </div>
        </div>

        <!-- PostgreSQL -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>PostgreSQL + PostGIS</h3>
            <span class="sys-status ok">
              <span class="sys-dot"></span>
              Conectado
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>Host</span><span class="font-mono">agrocycle_db</span></div>
            <div class="sys-kv"><span>Puerto</span><span class="font-mono">5434</span></div>
            <div class="sys-kv"><span>Base de datos</span><span class="font-mono">agrocycle</span></div>
            <div class="sys-kv"><span>PostGIS</span><span>Habilitado</span></div>
          </div>
        </div>

        <!-- Redis -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>Redis + Celery</h3>
            <span class="sys-status ok">
              <span class="sys-dot"></span>
              Activo
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>Puerto</span><span class="font-mono">6380</span></div>
            <div class="sys-kv"><span>Uso</span><span>Cache · Rate limiting</span></div>
            <div class="sys-kv"><span>Celery</span><span>Worker activo</span></div>
            <div class="sys-kv"><span>Tareas</span><span>Cola procesada</span></div>
          </div>
        </div>

        <!-- Open-Meteo -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>Open-Meteo API</h3>
            <span class="sys-status ok">
              <span class="sys-dot"></span>
              Conectado
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>URL</span><span class="font-mono">api.open-meteo.com</span></div>
            <div class="sys-kv"><span>Tipo</span><span>Histórico + Forecast</span></div>
            <div class="sys-kv"><span>Modelo</span><span>ERA5 · FAO-56</span></div>
            <div class="sys-kv"><span>Costo</span><span>Gratuito (Open Source)</span></div>
          </div>
        </div>

        <!-- OpenTopoData -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>OpenTopoData / NASA SRTM</h3>
            <span class="sys-status ok">
              <span class="sys-dot"></span>
              Conectado
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>URL</span><span class="font-mono">api.opentopodata.org</span></div>
            <div class="sys-kv"><span>Dataset</span><span>NASA SRTM 30m</span></div>
            <div class="sys-kv"><span>Uso</span><span>Topografía · Pendiente</span></div>
            <div class="sys-kv"><span>Algoritmo</span><span>Horn (1981)</span></div>
          </div>
        </div>

        <!-- Modelos predictivos -->
        <div class="sys-card">
          <div class="sys-card__header">
            <h3>Modelos predictivos</h3>
            <span class="sys-status warn">
              <span class="sys-dot"></span>
              v1 · FAO-33
            </span>
          </div>
          <div class="sys-info">
            <div class="sys-kv"><span>Estimación</span><span>FAO-33 (implementado)</span></div>
            <div class="sys-kv"><span>Balance hídrico</span><span>FAO-56 (implementado)</span></div>
            <div class="sys-kv"><span>ML Ridge Regression</span><span>v2 · Post temporada 2027</span></div>
            <div class="sys-kv"><span>Framework</span><span>scikit-learn (planificado)</span></div>
          </div>
        </div>

      </div>

      <!-- Info del proyecto -->
      <div class="sys-card sys-card--proyecto">
        <div class="sys-card__header">
          <h3>Información del proyecto</h3>
        </div>
        <div class="sys-info sys-info--grid">
          <div class="sys-kv"><span>Nombre</span><span>AgroCycle v1.0</span></div>
          <div class="sys-kv"><span>Institución</span><span>Universidad Nacional de Loja</span></div>
          <div class="sys-kv"><span>Zona de aplicación</span><span>Bosque seco, Sur del Ecuador</span></div>
          <div class="sys-kv"><span>Cultivo objetivo</span><span>Maíz (Zea mays)</span></div>
          <div class="sys-kv"><span>Validación</span><span>Temporada 2027 · Bramaderos, Loja</span></div>
          <div class="sys-kv"><span>Primer usuario</span><span>Finca Ramos · Agricultor real</span></div>
        </div>
      </div>

    </div>
  `,
  styles: [`
    @use '../../../../styles' as *;
    .sys-page{display:flex;flex-direction:column;gap:$s4;animation:fadeIn .2s ease}
    .sys-header{padding-bottom:$s4;border-bottom:1px solid var(--border); h1{font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:3px} p{font-size:12px;color:var(--text-sec)}}
    .sys-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:$s3; @media(max-width:900px){grid-template-columns:repeat(2,1fr)} @media(max-width:600px){grid-template-columns:1fr}}
    .sys-card{background:var(--bg-surface);border:1px solid var(--border);border-radius:$radius-md;overflow:hidden;
      &__header{display:flex;align-items:center;justify-content:space-between;padding:$s3 $s4;border-bottom:1px solid var(--border);gap:$s3; h3{font-size:13px;font-weight:600;color:var(--text-primary)}}
      &--proyecto{margin-top:$s1}
    }
    .sys-status{display:flex;align-items:center;gap:$s2;font-size:11px;font-weight:600;white-space:nowrap;
      &.ok{color:#2E7D32} &.warn{color:#F57C00} &.error{color:#D32F2F}
    }
    .sys-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;background:currentColor;animation:pulse-dot 2s infinite}
    .sys-info{padding:$s3 $s4;display:flex;flex-direction:column;gap:$s2;
      &--grid{display:grid;grid-template-columns:repeat(3,1fr);gap:$s2; @media(max-width:600px){grid-template-columns:1fr}}
    }
    .sys-kv{display:flex;flex-direction:column;gap:1px;
      span:first-child{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--text-ter)}
      span:last-child{font-size:12px;font-weight:500;color:var(--text-primary)}
    }
  `]
})
export class AdminSistemaComponent {}