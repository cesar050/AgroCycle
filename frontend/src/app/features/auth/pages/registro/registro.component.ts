import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

type Rol = 'agricultor' | 'agronomo' | null;

interface PasswordStrength {
  longitud: boolean;
  mayuscula: boolean;
  numero: boolean;
  especial: boolean;
}

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './registro.component.html',
  styleUrl: './registro.component.scss'
})
export class RegistroComponent {

  // Paso actual del registro
  paso = signal<1 | 2 | 3>(1);

  // Selección de rol
  rolSeleccionado = signal<Rol>(null);

  // Formulario
  nombre = '';
  apellido = '';
  correo = '';
  password = '';
  confirmarPassword = '';
  numeroRegistro = '';
  especialidad = '';
  aceptaTerminos = false;

  // Estado
  cargando = signal(false);
  error = signal('');
  exito = signal(false);
  mostrarPassword = signal(false);
  mostrarConfirmar = signal(false);

  // Fortaleza de contraseña
  fortaleza = signal<PasswordStrength>({
    longitud: false,
    mayuscula: false,
    numero: false,
    especial: false,
  });

  constructor(private authService: AuthService) {}

  // ----------------------------------------------------------------
  // Paso 1 — Selección de rol
  // ----------------------------------------------------------------
  seleccionarRol(rol: Rol) {
    this.rolSeleccionado.set(rol);
    this.paso.set(2);
  }

  // ----------------------------------------------------------------
  // Paso 2 — Formulario
  // ----------------------------------------------------------------
  evaluarPassword() {
    const p = this.password;
    this.fortaleza.set({
      longitud:  p.length >= 8,
      mayuscula: /[A-Z]/.test(p),
      numero:    /[0-9]/.test(p),
      especial:  /[!@#$%^&*(),.?":{}|<>]/.test(p),
    });
  }

  get fortalezaNivel(): number {
    const f = this.fortaleza();
    return [f.longitud, f.mayuscula, f.numero, f.especial]
      .filter(Boolean).length;
  }

  get fortalezaTexto(): string {
    switch (this.fortalezaNivel) {
      case 0:
      case 1: return 'Muy débil';
      case 2: return 'Débil';
      case 3: return 'Aceptable';
      case 4: return 'Fuerte';
      default: return '';
    }
  }

  get fortalezaColor(): string {
    switch (this.fortalezaNivel) {
      case 0:
      case 1: return '#DC2626';
      case 2: return '#EA580C';
      case 3: return '#CA8A04';
      case 4: return '#16A34A';
      default: return '#E2E2E2';
    }
  }

  validarPaso2(): string {
    if (!this.nombre.trim()) return 'Ingresa tu nombre.';
    if (!this.apellido.trim()) return 'Ingresa tu apellido.';
    if (!this.correo.includes('@')) return 'Ingresa un correo válido.';
    if (this.fortalezaNivel < 3) return 'La contraseña es muy débil.';
    if (this.password !== this.confirmarPassword)
      return 'Las contraseñas no coinciden.';
    if (this.rolSeleccionado() === 'agronomo' && !this.numeroRegistro.trim())
      return 'El número de registro profesional es requerido para agronomos.';
    if (!this.aceptaTerminos)
      return 'Debes aceptar los términos y condiciones.';
    return '';
  }

  irAPaso3() {
    const error = this.validarPaso2();
    if (error) {
      this.error.set(error);
      return;
    }
    this.error.set('');
    this.paso.set(3);
  }

  // ----------------------------------------------------------------
  // Paso 3 — Confirmación y envío
  // ----------------------------------------------------------------
  onSubmit() {
    this.cargando.set(true);
    this.error.set('');

    const rol_id = this.rolSeleccionado() === 'agricultor' ? 2 : 3;

    const datos: any = {
      nombre: this.nombre.trim(),
      apellido: this.apellido.trim(),
      correo: this.correo.toLowerCase().trim(),
      password: this.password,
      rol_id,
    };

    if (rol_id === 3) {
      datos.numero_registro = this.numeroRegistro.trim();
      datos.especialidad = this.especialidad.trim();
    }

    this.authService.registro(datos).subscribe({
      next: () => {
        this.cargando.set(false);
        this.exito.set(true);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.error?.error || 'Error al crear la cuenta. Intenta de nuevo.'
        );
        this.paso.set(2);
      }
    });
  }

  togglePassword()  { this.mostrarPassword.update(v => !v); }
  toggleConfirmar() { this.mostrarConfirmar.update(v => !v); }
  volver()          { this.paso.update(p => (p > 1 ? (p - 1) as 1|2|3 : 1)); }
}