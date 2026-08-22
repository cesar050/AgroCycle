import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class AdminService {

  constructor(private api: ApiService) {}

  listarUsuarios(params?: any): Observable<any> {
    return this.api.get('/admin/usuarios', params);
  }

  obtenerUsuario(id: string): Observable<any> {
    return this.api.get(`/admin/usuarios/${id}`);
  }

  editarUsuario(id: string, datos: any): Observable<any> {
    return this.api.put(`/admin/usuarios/${id}`, datos);
  }

  cambiarEstado(id: string, activo: boolean): Observable<any> {
    return this.api.patch(`/admin/usuarios/${id}/estado`, { activo });
  }

  // Métricas globales usando endpoints existentes
  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }

  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }
}