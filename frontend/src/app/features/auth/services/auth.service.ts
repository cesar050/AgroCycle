import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Usuario {
  id: string;
  nombre: string;
  correo: string;
  rol_id: number;
}

export interface LoginResponse {
  access_token?: string;
  refresh_token?: string;
  usuario?: Usuario;
  requiere_2fa?: boolean;
  token_temporal?: string;
  mensaje?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly API = environment.apiUrl;

  // Estado reactivo del usuario actual
  usuarioActual = signal<Usuario | null>(null);
  tokenTemporal = signal<string | null>(null);

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {
    // Restaurar sesión al recargar la página
    this.restaurarSesion();
  }

  // ----------------------------------------------------------------
  // Login
  // ----------------------------------------------------------------
  login(correo: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(
      `${this.API}/auth/login`,
      { correo, password }
    ).pipe(
      tap(res => {
        if (res.requiere_2fa && res.token_temporal) {
          // Guardar token temporal para el segundo paso
          this.tokenTemporal.set(res.token_temporal);
        } else if (res.access_token && res.usuario) {
          this.guardarSesion(res.access_token, res.refresh_token!, res.usuario);
        }
      })
    );
  }

  verificar2FA(codigo: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(
      `${this.API}/auth/2fa/verificar-login`,
      { codigo },
      { headers: { Authorization: `Bearer ${this.tokenTemporal()}` } }
    ).pipe(
      tap(res => {
        if (res.access_token && res.usuario) {
          this.guardarSesion(res.access_token, res.refresh_token!, res.usuario);
          this.tokenTemporal.set(null);
        }
      })
    );
  }

  // ----------------------------------------------------------------
  // Registro
  // ----------------------------------------------------------------
  registro(datos: any): Observable<any> {
    return this.http.post(`${this.API}/auth/registro`, datos);
  }

  // ----------------------------------------------------------------
  // Recuperar contraseña
  // ----------------------------------------------------------------
  recuperarPassword(correo: string): Observable<any> {
    return this.http.post(`${this.API}/auth/recuperar-password`, { correo });
  }

  resetearPassword(token: string, nueva_password: string): Observable<any> {
    return this.http.post(`${this.API}/auth/reset-password`, {
      token,
      nueva_password,
    });
  }

  verificarTokenReset(token: string): Observable<any> {
    return this.http.get(`${this.API}/auth/verificar-token-reset/${token}`);
  }

  verificarCorreo(token: string): Observable<any> {
    return this.http.get(`${this.API}/auth/verificar/${token}`);
  }

  // ----------------------------------------------------------------
  // Sesión
  // ----------------------------------------------------------------
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('usuario');
    this.usuarioActual.set(null);
    this.router.navigate(['/auth/login']);
  }

  get token(): string | null {
    return localStorage.getItem('access_token');
  }

  get estaAutenticado(): boolean {
    return !!this.token;
  }

  get rolUsuario(): number | null {
    const usuario = this.usuarioActual();
    return usuario ? usuario.rol_id : null;
  }

  get esAgricultor(): boolean { return this.rolUsuario === 2; }
  get esAgronomo(): boolean   { return this.rolUsuario === 3; }
  get esAdmin(): boolean      { return this.rolUsuario === 1; }

  private guardarSesion(
    token: string, refresh: string, usuario: Usuario
  ): void {
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('usuario', JSON.stringify(usuario));
    this.usuarioActual.set(usuario);
    this.redirigirSegunRol(usuario.rol_id);
  }

  private restaurarSesion(): void {
    const usuarioStr = localStorage.getItem('usuario');
    if (usuarioStr && this.token) {
      this.usuarioActual.set(JSON.parse(usuarioStr));
    }
  }

  private redirigirSegunRol(rol_id: number): void {
    switch (rol_id) {
      case 1: this.router.navigate(['/admin/dashboard']); break;
      case 2: this.router.navigate(['/app/dashboard']); break;
      case 3: this.router.navigate(['/agronomo/dashboard']); break;
      default: this.router.navigate(['/']);
    }
  }
}