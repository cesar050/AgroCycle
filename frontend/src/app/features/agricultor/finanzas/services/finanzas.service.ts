import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class FinanzasService {

  constructor(private api: ApiService) {}

  listarGastos(temporadaId: string): Observable<any> {
    return this.api.get(`/financiero/temporadas/${temporadaId}/gastos`);
  }

  calcularRentabilidad(temporadaId: string): Observable<any> {
    return this.api.get(
      `/financiero/temporadas/${temporadaId}/rentabilidad`
    );
  }

  registrarCompra(temporadaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/financiero/temporadas/${temporadaId}/compras`, datos
    );
  }

  eliminarCompra(compraId: string): Observable<any> {
    return this.api.delete(`/financiero/compras/${compraId}`);
  }

  registrarVenta(tpId: string, datos: any): Observable<any> {
    return this.api.post(
      `/financiero/temporada-parcela/${tpId}/venta`, datos
    );
  }

  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }

  listarParcelas(loteId: string): Observable<any> {
    return this.api.get(`/lotes/${loteId}/parcelas`);
  }

  listarLotes(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/lotes`);
  }

  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }
}