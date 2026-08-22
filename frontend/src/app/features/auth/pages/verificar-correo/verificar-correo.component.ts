import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-verificar-correo',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './verificar-correo.component.html',
  styleUrl: './verificar-correo.component.scss'
})
export class VerificarCorreoComponent implements OnInit {
  estado = signal<'cargando' | 'exito' | 'error'>('cargando');

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
  ) {}

  ngOnInit() {
    const token = this.route.snapshot.paramMap.get('token') || '';
    this.authService.verificarCorreo(token).subscribe({
      next: () => this.estado.set('exito'),
      error: () => this.estado.set('error'),
    });
  }
}