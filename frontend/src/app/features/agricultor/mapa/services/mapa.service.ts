import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class MapaService {

  constructor(private api: ApiService) {}

  // Fincas
  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }

  registrarFinca(datos: any): Observable<any> {
    return this.api.post('/fincas', datos);
  }

  obtenerMapaFinca(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/mapa`);
  }

  // Lotes
  listarLotes(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/lotes`);
  }

  registrarLote(fincaId: string, datos: any): Observable<any> {
    return this.api.post(`/fincas/${fincaId}/lotes`, datos);
  }

  // Parcelas
  listarParcelas(loteId: string): Observable<any> {
    return this.api.get(`/lotes/${loteId}/parcelas`);
  }

  registrarParcela(loteId: string, datos: any): Observable<any> {
    return this.api.post(`/lotes/${loteId}/parcelas`, datos);
  }

  // Topografía
  grillaTopo(parcelaId: string): Observable<any> {
    return this.api.get(`/parcelas/${parcelaId}/grilla-topografica`);
  }

  // En mapa.service.ts agrega:
  obtenerTopografiaFinca(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/mapa/topografia`);
  }
}