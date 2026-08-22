import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class ClimaticoService {

  constructor(private api: ApiService) {}

  listarClima(parcelaId: string): Observable<any> {
    return this.api.get(`/climatico/parcelas/${parcelaId}/clima`);
  }

  historialClimatico(
    parcelaId: string,
    params?: any
  ): Observable<any> {
    return this.api.get(
      `/climatico/parcelas/${parcelaId}/historial`, params
    );
  }

  forecast(parcelaId: string): Observable<any> {
    return this.api.get(
      `/climatico/parcelas/${parcelaId}/forecast`
    );
  }

  descargarClima(parcelaId: string, datos: any): Observable<any> {
    return this.api.post(
      `/climatico/parcelas/${parcelaId}/clima`, datos
    );
  }

  registrarEventoManual(
    parcelaId: string, datos: any
  ): Observable<any> {
    return this.api.post(
      `/climatico/parcelas/${parcelaId}/evento-manual`, datos
    );
  }

  calcularBalanceHidrico(tpId: string): Observable<any> {
    return this.api.post(
      `/climatico/temporada-parcelas/${tpId}/balance-hidrico`, {}
    );
  }

  calcularEstresHidrico(tpId: string): Observable<any> {
    return this.api.post(
      `/climatico/temporada-parcelas/${tpId}/estres-hidrico`, {}
    );
  }

  generarAlertas(): Observable<any> {
    return this.api.get('/climatico/alertas');
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

  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas/historial');
  }
}