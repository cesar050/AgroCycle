import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-recuperar-password',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './recuperar-password.component.html',
  styleUrl: './recuperar-password.component.scss'
})
export class RecuperarPasswordComponent {
  correo = '';
  cargando = signal(false);
  error = signal('');
  enviado = signal(false);

  constructor(private authService: AuthService) {}

  onSubmit() {
    if (!this.correo.includes('@')) {
      this.error.set('Ingresa un correo electrónico válido.');
      return;
    }

    this.cargando.set(true);
    this.error.set('');

    this.authService.recuperarPassword(this.correo).subscribe({
      next: () => {
        this.cargando.set(false);
        this.enviado.set(true);
      },
      error: () => {
        this.cargando.set(false);
        // Mostrar mismo mensaje por seguridad
        this.enviado.set(true);
      }
    });
  }
}