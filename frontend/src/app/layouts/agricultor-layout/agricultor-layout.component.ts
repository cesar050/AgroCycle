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
  '/app/dashboard':       { titulo: 'Inicio',         sub: 'Resumen general de tu actividad agrícola' },
  '/app/mapa':            { titulo: 'Mapa de la Finca', sub: 'Visualiza tus lotes y parcelas' },
  '/app/temporada':       { titulo: 'Temporadas',      sub: 'Gestión de temporadas de siembra' },
  '/app/actividades':     { titulo: 'Actividades',     sub: 'Registro de actividades de campo' },
  '/app/climatico':       { titulo: 'Clima y Agua',    sub: 'Datos climáticos e indicadores hídricos' },
  '/app/finanzas':        { titulo: 'Finanzas',        sub: 'Control económico de la temporada' },
  '/app/reportes':        { titulo: 'Reportes',        sub: 'Fichas técnicas y documentos' },
  '/app/recomendaciones': { titulo: 'Recomendaciones', sub: 'Recomendaciones del agrónomo' },
};

@Component({
  selector: 'app-agricultor-layout',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './agricultor-layout.component.html',
  styleUrl: './agricultor-layout.component.scss'
})
export class AgricultorLayoutComponent implements OnInit {
  sidebarAbierto = signal(false);
  darkMode       = signal(false);
  mapaAbierto    = signal(false);
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

    // Actualizar título según la ruta
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe((e: any) => {
        const info = RUTAS[e.urlAfterRedirects] || RUTAS[e.url] || { titulo: 'AgroCycle' };
        this.tituloActual    = info.titulo;
        this.subtituloActual = info.sub || '';
        if (this.esMobile()) this.sidebarAbierto.set(false);
      });

    // Estado inicial del título
    const info = RUTAS[this.router.url] || { titulo: 'Inicio', sub: 'Resumen general' };
    this.tituloActual    = info.titulo;
    this.subtituloActual = info.sub || '';
  }

  @HostListener('window:resize')
  onResize() {
    this.esMobile.set(window.innerWidth < 1024);
  }

  private actualizarFecha() {
    const ahora = new Date();
    const opciones: Intl.DateTimeFormatOptions = {
      day: 'numeric', month: 'short', year: 'numeric'
    };
    this.fechaHoy = ahora.toLocaleDateString('es-EC', opciones);
  }

  toggleSidebar()    { this.sidebarAbierto.update(v => !v); }
  cerrarSidebar()    { this.sidebarAbierto.set(false); }
  cerrarSidebarMobile() {
    if (this.esMobile()) this.sidebarAbierto.set(false);
  }

  toggleMapa() {
    this.mapaAbierto.update(v => !v);
  }

  mapaActivo(): boolean {
    return this.router.url.startsWith('/app/mapa');
  }

  toggleDark() {
    this.darkMode.update(v => !v);
    document.body.classList.toggle('dark');
  }

  cerrarSesion() {
    this.authService.logout();
  }

  get usuario() {
    return this.authService.usuarioActual();
  }

  get iniciales(): string {
    const n = this.usuario?.nombre || '';
    const partes = n.trim().split(' ');
    if (partes.length >= 2) {
      return `${partes[0][0]}${partes[1][0]}`.toUpperCase();
    }
    return partes[0]?.[0]?.toUpperCase() || 'U';
  }
}