import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  // Formulario
  correo = '';
  password = '';
  codigo2FA = '';
  recordarme = false;

  // Estado
  cargando = signal(false);
  error = signal('');
  requiere2FA = signal(false);
  mostrarPassword = signal(false);

  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}

  onSubmit() {
    if (!this.correo || !this.password) {
      this.error.set('Ingresa tu correo y contraseña.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    this.authService.login(this.correo, this.password).subscribe({
      next: (res) => {
        this.cargando.set(false);
        if (res.requiere_2fa) {
          this.requiere2FA.set(true);
        }
        // Si no requiere 2FA el AuthService ya redirige
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.error?.error || 'Correo o contraseña incorrectos.'
        );
      }
    });
  }

  onVerificar2FA() {
    if (!this.codigo2FA || this.codigo2FA.length !== 6) {
      this.error.set('Ingresa el código de 6 dígitos de tu app.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    this.authService.verificar2FA(this.codigo2FA).subscribe({
      next: () => {
        this.cargando.set(false);
        // AuthService redirige automáticamente según el rol
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.error?.error || 'Código incorrecto. Intenta de nuevo.'
        );
      }
    });
  }

  togglePassword() {
    this.mostrarPassword.update(v => !v);
  }

  volver2FA() {
    this.requiere2FA.set(false);
    this.codigo2FA = '';
    this.error.set('');
  }
}