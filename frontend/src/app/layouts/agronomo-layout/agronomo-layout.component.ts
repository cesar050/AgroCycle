import {
  Component, signal, HostListener, OnInit
} from '@angular/core';
import {
  CommonModule
} from '@angular/common';
import {
  RouterLink, RouterLinkActive, RouterOutlet,
  Router, NavigationEnd
} from '@angular/router';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/auth.service';

const RUTAS: Record<string, { titulo: string; sub?: string }> = {
  '/agronomo/dashboard':       { titulo: 'Inicio',           sub: 'Panel de control del agrónomo' },
  '/agronomo/fincas':          { titulo: 'Fincas asignadas', sub: 'Fincas y cultivos bajo tu seguimiento' },
  '/agronomo/observaciones':   { titulo: 'Observaciones',    sub: 'Registro de observaciones técnicas de campo' },
  '/agronomo/recomendaciones': { titulo: 'Recomendaciones',  sub: 'Recomendaciones emitidas a los agricultores' },
  '/agronomo/evaluaciones':    { titulo: 'Evaluaciones',     sub: 'Evaluaciones de campo registradas' },
};

@Component({
  selector: 'app-agronomo-layout',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './agronomo-layout.component.html',
  styleUrl: './agronomo-layout.component.scss'
})
export class AgronomoLayoutComponent implements OnInit {
  sidebarAbierto = signal(false);
  darkMode       = signal(false);
  esMobile       = signal(window.innerWidth < 1024);
  tituloActual    = 'Inicio';
  subtituloActual = '';
  fechaHoy        = '';

  constructor(
    public authService: AuthService,
    private router: Router,
  ) {}

  ngOnInit() {
    this.actualizarFecha();
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe((e: any) => {
        const info = RUTAS[e.urlAfterRedirects] || { titulo: 'AgroCycle' };
        this.tituloActual    = info.titulo;
        this.subtituloActual = info.sub || '';
        if (this.esMobile()) this.sidebarAbierto.set(false);
      });
    const info = RUTAS[this.router.url] || { titulo: 'Inicio' };
    this.tituloActual    = info.titulo;
    this.subtituloActual = info.sub || '';
  }

  @HostListener('window:resize')
  onResize() { this.esMobile.set(window.innerWidth < 1024); }

  private actualizarFecha() {
    this.fechaHoy = new Date().toLocaleDateString('es-EC', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  }

  toggleSidebar()      { this.sidebarAbierto.update(v => !v); }
  cerrarSidebar()      { this.sidebarAbierto.set(false); }
  cerrarSidebarMobile() { if (this.esMobile()) this.sidebarAbierto.set(false); }
  toggleDark()         { this.darkMode.update(v => !v); document.body.classList.toggle('dark'); }
  cerrarSesion()       { this.authService.logout(); }

  get usuario() { return this.authService.usuarioActual(); }

  get iniciales(): string {
    const n = this.usuario?.nombre || '';
    const p = n.trim().split(' ');
    return p.length >= 2
      ? `${p[0][0]}${p[1][0]}`.toUpperCase()
      : p[0]?.[0]?.toUpperCase() || 'A';
  }
}