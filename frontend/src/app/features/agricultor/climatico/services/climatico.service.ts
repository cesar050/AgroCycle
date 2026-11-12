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

  calcularBalanceHidrico(tpId: string, body: any): Observable<any> {
    return this.api.post(
      `/climatico/temporada-parcelas/${tpId}/balance-hidrico`, body
    );
  }

  calcularEstresHidrico(tpId: string, body: any): Observable<any> {
    return this.api.post(
      `/climatico/temporada-parcelas/${tpId}/estres-hidrico`, body
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

  // Temporadas del agricultor (incluye estado). Se usa para localizar
  // la temporada_parcela activa que alimenta balance/estres hidrico.
  listarTemporadas(): Observable<any> {
    return this.api.get('/temporadas');
  }

  obtenerTemporada(temporadaId: string): Observable<any> {
    return this.api.get(`/temporadas/${temporadaId}`);
  }
}