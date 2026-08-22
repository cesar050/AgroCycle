import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class TemporadaService {

  constructor(private api: ApiService) {}

  listar(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }

  obtener(id: string): Observable<any> {
    return this.api.get(`/temporadas/${id}`);
  }

  registrar(datos: any): Observable<any> {
    return this.api.post('/temporadas', datos);
  }

  vincularParcela(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(`/temporadas/${temporadaId}/parcelas`, datos);
  }

  actualizarFenologia(temporadaId: string, datos: any): Observable<any> {
    return this.api.patch(`/temporadas/${temporadaId}/fenologia`, datos);
  }

  cerrar(temporadaId: string, datos: any): Observable<any> {
    return this.api.patch(`/temporadas/${temporadaId}/cerrar`, datos);
  }

  cancelar(temporadaId: string): Observable<any> {
    return this.api.patch(`/temporadas/${temporadaId}/cancelar`, {});
  }

  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }

  listarLotes(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/lotes`);
  }

  listarParcelas(loteId: string): Observable<any> {
    return this.api.get(`/lotes/${loteId}/parcelas`);
  }

  generarEstimacion(tpId: string): Observable<any> {
    return this.api.post(
      `/estimacion/temporada-parcela/${tpId}/estimar`, {}
    );
  }

  obtenerEstimaciones(temporadaId: string): Observable<any> {
    return this.api.get(
      `/estimacion/temporada/${temporadaId}/estimaciones`
    );
  }
}