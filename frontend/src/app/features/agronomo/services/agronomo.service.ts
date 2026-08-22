import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class AgronomoService {

  constructor(private api: ApiService) {}

  // Temporadas asignadas al agrónomo
  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }

  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }

  // Observaciones
  listarObservaciones(temporadaId: string): Observable<any> {
    return this.api.get(
      `/agronomo/temporadas/${temporadaId}/observaciones`
    );
  }

  registrarObservacion(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/agronomo/temporadas/${temporadaId}/observaciones`, datos
    );
  }

  // Recomendaciones
  listarRecomendaciones(temporadaId: string): Observable<any> {
    return this.api.get(
      `/agronomo/temporadas/${temporadaId}/recomendaciones`
    );
  }

  registrarRecomendacion(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/agronomo/temporadas/${temporadaId}/recomendaciones`, datos
    );
  }

  // Evaluaciones
  listarEvaluaciones(temporadaId: string): Observable<any> {
    return this.api.get(
      `/agronomo/temporadas/${temporadaId}/evaluaciones`
    );
  }

  registrarEvaluacion(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/agronomo/temporadas/${temporadaId}/evaluaciones`, datos
    );
  }

  // Clima para contexto
  listarClima(parcelaId: string): Observable<any> {
    return this.api.get(`/climatico/parcelas/${parcelaId}/clima`);
  }
}