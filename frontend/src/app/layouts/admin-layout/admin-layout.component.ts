import {
  Component, OnInit, signal, HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  RouterLink, RouterLinkActive, RouterOutlet,
  Router, NavigationEnd
} from '@angular/router';
import { filter } from 'rxjs/operators';
import { AuthService } from '../../features/auth/services/auth.service';

const RUTAS: Record<string, { titulo: string; sub: string }> = {
  '/admin/dashboard': { titulo: 'Panel de control', sub: 'Resumen general del sistema AgroCycle' },
  '/admin/usuarios':  { titulo: 'Gestión de usuarios', sub: 'Administra agricultores, agrónomos y administradores' },
  '/admin/fincas':    { titulo: 'Fincas del sistema', sub: 'Todas las fincas registradas en la plataforma' },
  '/admin/sistema':   { titulo: 'Monitor del sistema', sub: 'Estado de servicios y configuración' },
};

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './admin-layout.component.html',
  styleUrl: './admin-layout.component.scss'
})
export class AdminLayoutComponent implements OnInit {
  sidebarAbierto = signal(false);
  darkMode       = signal(false);
  esMobile       = signal(window.innerWidth < 1024);
  tituloActual    = 'Panel de control';
  subtituloActual = '';
  fechaHoy        = '';

  constructor(public authService: AuthService, private router: Router) {}

  ngOnInit() {
    this.fechaHoy = new Date().toLocaleDateString('es-EC', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe((e: any) => {
        const info = RUTAS[e.urlAfterRedirects] || { titulo: 'Admin', sub: '' };
        this.tituloActual    = info.titulo;
        this.subtituloActual = info.sub;
        if (this.esMobile()) this.sidebarAbierto.set(false);
      });
    const info = RUTAS[this.router.url] || { titulo: 'Panel de control', sub: '' };
    this.tituloActual    = info.titulo;
    this.subtituloActual = info.sub;
  }

  @HostListener('window:resize')
  onResize() { this.esMobile.set(window.innerWidth < 1024); }

  toggleSidebar()       { this.sidebarAbierto.update(v => !v); }
  cerrarSidebar()       { this.sidebarAbierto.set(false); }
  cerrarSidebarMobile() { if (this.esMobile()) this.sidebarAbierto.set(false); }
  toggleDark()          { this.darkMode.update(v => !v); document.body.classList.toggle('dark'); }
  cerrarSesion()        { this.authService.logout(); }

  get usuario() { return this.authService.usuarioActual(); }

  get iniciales(): string {
    const n = this.usuario?.nombre || 'A';
    const p = n.trim().split(' ');
    return p.length >= 2
      ? `${p[0][0]}${p[1][0]}`.toUpperCase()
      : p[0]?.[0]?.toUpperCase() || 'A';
  }
}