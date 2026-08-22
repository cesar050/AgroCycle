import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './reset-password.component.html',
  styleUrl: './reset-password.component.scss'
})
export class ResetPasswordComponent implements OnInit {
  token = '';
  tokenValido = signal<boolean | null>(null);
  nombreUsuario = signal('');

  nuevaPassword = '';
  confirmarPassword = '';
  mostrarPassword = signal(false);
  cargando = signal(false);
  error = signal('');
  exito = signal(false);

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
  ) {}

  ngOnInit() {
    this.token = this.route.snapshot.paramMap.get('token') || '';
    this.verificarToken();
  }

  verificarToken() {
    this.authService.verificarTokenReset(this.token).subscribe({
      next: (res) => {
        this.tokenValido.set(true);
        this.nombreUsuario.set(res.nombre);
      },
      error: () => {
        this.tokenValido.set(false);
      }
    });
  }

  get passwordsCoinciden(): boolean {
    return this.nuevaPassword === this.confirmarPassword;
  }

  onSubmit() {
    if (!this.nuevaPassword || this.nuevaPassword.length < 8) {
      this.error.set('La contraseña debe tener al menos 8 caracteres.');
      return;
    }
    if (!this.passwordsCoinciden) {
      this.error.set('Las contraseñas no coinciden.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    this.authService.resetearPassword(
      this.token, this.nuevaPassword
    ).subscribe({
      next: () => {
        this.cargando.set(false);
        this.exito.set(true);
      },
      error: (err) => {
        this.cargando.set(false);
        this.error.set(
          err.error?.error || 'Error al cambiar la contraseña.'
        );
      }
    });
  }

  togglePassword() { this.mostrarPassword.update(v => !v); }
}