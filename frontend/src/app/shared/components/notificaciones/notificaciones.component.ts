import { Component, inject } from '@angular/core';
import { NotificacionService } from '../../../core/services/notificacion.service';

@Component({
  selector: 'app-notificaciones',
  standalone: true,
  templateUrl: './notificaciones.component.html',
  styleUrl: './notificaciones.component.scss',
})
export class NotificacionesComponent {
  servicio = inject(NotificacionService);
}
