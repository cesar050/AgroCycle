import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class ActividadesService {

  constructor(private api: ApiService) {}

  listarPorTemporada(temporadaId: string): Observable<any> {
    return this.api.get(
      `/actividades/temporadas/${temporadaId}/actividades`
    );
  }

  registrar(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/actividades/temporadas/${temporadaId}/actividades`, datos
    );
  }

  eliminar(actividadId: string): Observable<any> {
    return this.api.delete(`/actividades/${actividadId}`);
  }

  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }
}