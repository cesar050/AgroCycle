import {
  Component, signal, effect, HostListener, OnInit, ViewChild, ElementRef
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
import { FincaContextService, Finca } from '../../core/services/finca-context.service';
import { DarkModeService } from '../../core/services/dark-mode.service';

const RUTAS: Record<string, { titulo: string; sub?: string }> = {
  '/app/dashboard':       { titulo: 'Resumen de mi finca', sub: 'Consulta el estado actual de tu terreno y cultivos' },
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
  sidebarAbierto       = signal(false);
  mapaAbierto          = signal(false);
  esMobile             = signal(window.innerWidth < 1024);
  selectorFincaAbierto = signal(false);
  menuPerfilAbierto    = signal(false);

  tituloActual    = 'Inicio';
  subtituloActual = '';
  fechaHoy        = '';

  @ViewChild('selectorFincaRef') selectorFincaRef!: ElementRef;
  @ViewChild('perfilMenuRef') perfilMenuRef!: ElementRef;

  constructor(
    public authService: AuthService,
    public fincaContext: FincaContextService,
    public darkModeService: DarkModeService,
    private router: Router,
  ) {
    // Cualquier vista (p. ej. el dashboard) puede pedir abrir el dropdown
    // de finca sin duplicar su lógica, a través de un signal compartido.
    effect(() => {
      if (this.fincaContext.selectorAbierto()) {
        this.selectorFincaAbierto.set(true);
        this.fincaContext.selectorAbierto.set(false);
      }
    });
  }

  get enDashboard(): boolean {
    return this.router.url.startsWith('/app/dashboard');
  }

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

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    if (
      this.selectorFincaAbierto() &&
      this.selectorFincaRef &&
      !this.selectorFincaRef.nativeElement.contains(event.target)
    ) {
      this.selectorFincaAbierto.set(false);
    }

    if (
      this.menuPerfilAbierto() &&
      this.perfilMenuRef &&
      !this.perfilMenuRef.nativeElement.contains(event.target)
    ) {
      this.menuPerfilAbierto.set(false);
    }
  }

  toggleSelectorFinca() {
    if (this.fincaContext.fincas().length <= 1) return;
    this.selectorFincaAbierto.update(v => !v);
  }

  toggleMenuPerfil() {
    this.menuPerfilAbierto.update(v => !v);
  }

  seleccionarFinca(finca: Finca) {
    this.fincaContext.seleccionarFinca(finca);
    this.selectorFincaAbierto.set(false);
  }

  private actualizarFecha() {
    const dias  = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const ahora = new Date();
    this.fechaHoy =
      `${dias[ahora.getDay()]}, ${ahora.getDate()} de ${meses[ahora.getMonth()]}. de ${ahora.getFullYear()}`;
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